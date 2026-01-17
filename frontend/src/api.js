const API_BASE = 'http://localhost:8000/api/v1';

async function fetchAPI(endpoint, options = {}) {
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

export async function sendInbox(text) {
  return fetchAPI('/inbox', {
    method: 'POST',
    body: JSON.stringify({ text }),
  });
}

export async function listPending(personId = null) {
  // The endpoint doesn't support person_id filter, so we filter client-side
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
  // Get all pending items and extract unique people
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

export async function listEvents() {
  // Endpoint doesn't exist yet, return empty array
  // When implemented, it should be GET /calendar/events
  return [];
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
    // If endpoint doesn't exist or returns error, return empty
    throw new Error('Outbox endpoint no disponible');
  }
}
