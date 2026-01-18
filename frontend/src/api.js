const API_BASE = 'http://localhost:8000/api/v1';

export async function fetchAPI(endpoint, options = {}) {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    throw error;
  }
}

export async function sendInbox(text, useLLM = true) {
  return fetchAPI('/inbox', {
    method: 'POST',
    body: JSON.stringify({ text, use_llm: useLLM }),
  });
}

export async function listPending(personId = null) {
  const items = await fetchAPI('/memory/pending');
  if (personId) {
    return items.filter(item => item.related_person_id === personId);
  }
  return items;
}

export async function listAllItems(status = null) {
  const url = status ? `/memory/items?status=${status}` : '/memory/items';
  return fetchAPI(url);
}

export async function listPeople() {
  const items = await listPending();
  const peopleMap = new Map();
  
  items.forEach(item => {
    if (item.related_person_id && item.related_person_name) {
      if (!peopleMap.has(item.related_person_id)) {
        peopleMap.set(item.related_person_id, {
          id: item.related_person_id,
          name: item.related_person_name,
        });
      }
    }
  });
  
  return Array.from(peopleMap.values());
}

export async function createEvent(title, startTime, endTime, personName = null) {
  return fetchAPI('/calendar/events', {
    method: 'POST',
    body: JSON.stringify({
      title,
      start_time: startTime,
      end_time: endTime,
      person_name: personName,
    }),
  });
}

export async function getBriefing(eventId) {
  return fetchAPI(`/calendar/events/${eventId}/briefing`);
}

export async function closeEvent(eventId, discussedItemIds) {
  return fetchAPI(`/calendar/events/${eventId}/close`, {
    method: 'POST',
    body: JSON.stringify({
      discussed_item_ids: discussedItemIds,
    }),
  });
}

export async function listOutbox(status = null) {
  try {
    const url = status ? `/outbox?status=${status}` : '/outbox';
    return await fetchAPI(url);
  } catch (err) {
    throw new Error('Outbox endpoint no disponible');
  }
}

export async function markItemAsDiscussed(itemId) {
  // Use the close event endpoint with a fake event or create a debug endpoint
  // For now, we'll use a workaround: create a temporary event and close it
  // This is a debug function, so it's acceptable
  try {
    // Create a temporary event
    const now = new Date();
    const event = await createEvent(
      `Debug: Mark item ${itemId} as discussed`,
      now.toISOString(),
      new Date(now.getTime() + 60000).toISOString(),
      null
    );
    
    // Close the event with this item
    await closeEvent(event.id, [itemId]);
    
    return { ok: true, message: 'Item marcado como discutido' };
  } catch (err) {
    throw new Error(`Error al marcar item: ${err.message}`);
  }
}

// Briefing API
export async function getBriefingForPerson(personId) {
  return fetchAPI(`/briefing/${personId}`);
}

export async function closeBriefing(personId, itemIds) {
  return fetchAPI(`/briefing/${personId}/close`, {
    method: 'POST',
    body: JSON.stringify({ item_ids: itemIds }),
  });
}

// Prompt Lab API
export async function listPromptBlocks() {
  return fetchAPI('/debug/prompt');
}

export async function savePromptBlock(block) {
  return fetchAPI('/debug/prompt', {
    method: 'POST',
    body: JSON.stringify(block),
  });
}

export async function deletePromptBlock(blockId) {
  return fetchAPI(`/debug/prompt/${blockId}`, {
    method: 'DELETE',
  });
}

export async function resetPromptBlocks() {
  return fetchAPI('/debug/prompt/reset', {
    method: 'POST',
  });
}

export async function getActivePrompt() {
  return fetchAPI('/debug/prompt/active');
}

export async function testPrompt(text) {
  return fetchAPI('/debug/prompt/test', {
    method: 'POST',
    body: JSON.stringify({ text }),
  });
}
