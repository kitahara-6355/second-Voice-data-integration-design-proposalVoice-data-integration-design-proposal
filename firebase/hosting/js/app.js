document.addEventListener('DOMContentLoaded', () => {
    // --- Configuration ---
    const firebaseConfig = {
        apiKey: "YOUR_API_KEY",
        authDomain: "YOUR_AUTH_DOMAIN",
        projectId: "YOUR_PROJECT_ID",
        storageBucket: "YOUR_STORAGE_BUCKET",
        messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
        appId: "YOUR_APP_ID"
    };
    const API_BASE_URL = "http://localhost:8000";

    // --- DOM Elements ---
    const meetingsList = document.getElementById('meetings-list');
    const loader = document.getElementById('loader');
    const searchForm = document.getElementById('search-form');
    const searchInput = document.getElementById('search-input');
    const resultsHeader = document.getElementById('results-header');

    // --- App State ---
    let meetingsData = {}; // Store all meeting data by ID for easy access

    // --- Firebase Initialization ---
    try {
        firebase.initializeApp(firebaseConfig);
    } catch (e) {
        console.error('Error initializing Firebase:', e);
        loader.textContent = 'Error: Could not initialize Firebase.';
        return;
    }
    const db = firebase.firestore();

    // --- PWA Service Worker ---
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js').catch(err => console.error('SW registration failed', err));
    }

    // --- Data Fetching and Rendering ---
    const fetchAndRenderMeetings = async () => {
        clearContent();
        showLoader('Loading meetings...');
        try {
            const snapshot = await db.collection('meetings').orderBy('date', 'desc').get();
            hideLoader();
            if (snapshot.empty) {
                updateResultsHeader('No meetings found in Firestore.');
                return;
            }
            meetingsData = {}; // Clear old data
            snapshot.forEach(doc => {
                meetingsData[doc.id] = doc.data();
            });
            updateResultsHeader(`Showing ${snapshot.size} most recent meetings.`);
            Object.values(meetingsData).forEach(meeting => {
                meetingsList.appendChild(createMeetingListItem(meeting));
            });
        } catch (error) {
            handleError('Failed to load meetings.', error);
        }
    };

    const performSearch = async (query) => {
        clearContent();
        showLoader(`Searching for "${query}"...`);
        try {
            const response = await fetch(`${API_BASE_URL}/search?q=${encodeURIComponent(query)}&top_k=10`);
            if (!response.ok) throw new Error(`API error: ${response.status}. Is the local API server running?`);
            const results = await response.json();
            hideLoader();
            renderSearchResults(query, results);
        } catch (error) {
            handleError('Search failed.', error);
        }
    };

    // --- UI Rendering ---
    const renderSearchResults = (query, results) => {
        const ids = results.ids?.[0];
        if (!ids || ids.length === 0) {
            updateResultsHeader(`No results found for "${query}".`, true);
            return;
        }
        updateResultsHeader(`Found ${ids.length} results for "${query}"`, true);
        ids.forEach((id, i) => {
            const result = {
                id: id,
                distance: results.distances[0][i],
                metadata: results.metadatas[0][i],
                document: results.documents[0][i]
            };
            meetingsList.appendChild(createSearchResultElement(result));
        });
    };

    const renderSingleMeeting = (meeting, highlightText = null) => {
        clearContent();
        updateResultsHeader(`Viewing: ${meeting.title}`, true);
        const meetingElement = createMeetingElement(meeting, highlightText);
        meetingsList.appendChild(meetingElement);

        if (highlightText) {
            const highlightedEl = document.getElementById('highlighted-segment');
            if (highlightedEl) {
                highlightedEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    };

    // --- Element Creators ---
    const createMeetingListItem = (meeting) => {
        const item = document.createElement('li');
        item.className = 'meeting-item';
        item.innerHTML = `<div class="meeting-header"><h2>${meeting.title}</h2><div class="date">${new Date(meeting.date).toLocaleString()}</div></div>`;
        item.addEventListener('click', () => renderSingleMeeting(meeting));
        return item;
    };

    const createMeetingElement = (meeting, highlightText) => {
        const item = document.createElement('li');
        item.className = 'meeting-item';
        const fullTranscriptHtml = meeting.full_transcript.split('\n').map(line => {
            if (highlightText && line.includes(highlightText)) {
                return `<span class="highlight" id="highlighted-segment">${line}</span>`;
            }
            return line;
        }).join('\n');

        item.innerHTML = `
            <div class="meeting-header"><h2>${meeting.title}</h2><div class="date">${new Date(meeting.date).toLocaleString()}</div></div>
            <div class="meeting-content visible">
                <h3>Summary</h3><p>${meeting.summary || 'N/A'}</p>
                <h3>Full Transcript</h3><pre>${fullTranscriptHtml || 'N/A'}</pre>
            </div>
        `;
        return item;
    };

    const createSearchResultElement = (result) => {
        const item = document.createElement('li');
        item.className = 'meeting-item clickable';
        const meetingId = result.metadata.meeting_id;
        item.innerHTML = `
            <div class="meeting-header"><h2>${meetingId}</h2><div class="date">Similarity: ${(1 - result.distance).toFixed(2)}</div></div>
            <div class="meeting-content visible"><p>"...${result.document}..."</p><p><em>(Time: ${result.metadata.start} - ${result.metadata.end})</em></p></div>
        `;
        item.addEventListener('click', () => {
            if (meetingsData[meetingId]) {
                renderSingleMeeting(meetingsData[meetingId], result.document);
            } else {
                alert(`Could not find full data for meeting ${meetingId}. Please clear search and try again.`);
            }
        });
        return item;
    };

    // --- UI Helpers ---
    const clearContent = () => {
        meetingsList.innerHTML = '';
        resultsHeader.innerHTML = '';
    };

    const updateResultsHeader = (text, showClearButton = false) => {
        resultsHeader.innerHTML = ''; // Clear previous content
        const textNode = document.createTextNode(text);
        resultsHeader.appendChild(textNode);
        if (showClearButton) {
            const button = document.createElement('button');
            button.textContent = 'Show All Meetings';
            button.onclick = fetchAndRenderMeetings;
            resultsHeader.appendChild(document.createElement('br'));
            resultsHeader.appendChild(button);
        }
    };

    const showLoader = (text) => {
        loader.textContent = text;
        loader.style.display = 'block';
    };

    const hideLoader = () => {
        loader.style.display = 'none';
    };

    const handleError = (message, error) => {
        console.error(message, error);
        hideLoader();
        updateResultsHeader(`${message} ${error.message}`);
    };

    // --- Event Listeners ---
    searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const query = searchInput.value.trim();
        if (query) performSearch(query);
    });

    // --- Initial Load ---
    fetchAndRenderMeetings();
});
