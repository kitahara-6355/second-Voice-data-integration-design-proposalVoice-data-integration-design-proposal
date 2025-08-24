document.addEventListener('DOMContentLoaded', () => {
    // --- Firebase Configuration ---
    const firebaseConfig = {
        apiKey: "YOUR_API_KEY",
        authDomain: "YOUR_AUTH_DOMAIN",
        projectId: "YOUR_PROJECT_ID",
        storageBucket: "YOUR_STORAGE_BUCKET",
        messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
        appId: "YOUR_APP_ID"
    };

    // --- API Configuration ---
    const API_BASE_URL = "http://localhost:8000";

    // --- DOM Elements ---
    const meetingsList = document.getElementById('meetings-list');
    const loader = document.getElementById('loader');
    const searchForm = document.getElementById('search-form');
    const searchInput = document.getElementById('search-input');
    const resultsHeader = document.getElementById('results-header');

    // --- Initialize Firebase and Firestore ---
    try {
        firebase.initializeApp(firebaseConfig);
    } catch (e) {
        console.error('Error initializing Firebase:', e);
        loader.textContent = 'Error: Could not initialize Firebase. Please check your configuration.';
        return;
    }
    const db = firebase.firestore();

    // --- PWA: Register Service Worker ---
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js')
            .then(reg => console.log('Service Worker registered', reg))
            .catch(err => console.error('Service Worker registration failed', err));
    }

    // --- Initial Data Load ---
    const fetchAndRenderMeetings = async () => {
        clearResults();
        loader.textContent = 'Loading meetings...';
        loader.style.display = 'block';

        try {
            const snapshot = await db.collection('meetings').orderBy('date', 'desc').get();
            loader.style.display = 'none';
            if (snapshot.empty) {
                resultsHeader.textContent = 'No meetings found in Firestore.';
                return;
            }
            resultsHeader.textContent = `Showing ${snapshot.size} most recent meetings.`;
            snapshot.forEach(doc => {
                const meeting = doc.data();
                const meetingItem = createMeetingElement(meeting);
                meetingsList.appendChild(meetingItem);
            });
        } catch (error) {
            console.error("Error fetching meetings:", error);
            loader.textContent = 'Failed to load meetings. Please check console for errors.';
        }
    };

    // --- Search Functionality ---
    const performSearch = async (query) => {
        clearResults();
        loader.textContent = `Searching for "${query}"...`;
        loader.style.display = 'block';

        try {
            const response = await fetch(`${API_BASE_URL}/search?q=${encodeURIComponent(query)}&top_k=10`);
            if (!response.ok) {
                throw new Error(`API request failed with status ${response.status}. Is the local API server running?`);
            }
            const results = await response.json();
            loader.style.display = 'none';
            renderSearchResults(query, results);
        } catch (error) {
            console.error("Search failed:", error);
            loader.textContent = `Search failed. ${error.message}`;
        }
    };

    const renderSearchResults = (query, results) => {
        const ids = results.ids && results.ids[0];
        if (!ids || ids.length === 0) {
            resultsHeader.textContent = `No results found for "${query}".`;
            addClearSearchButton();
            return;
        }

        resultsHeader.textContent = `Found ${ids.length} results for "${query}"`;
        addClearSearchButton();

        for (let i = 0; i < ids.length; i++) {
            const searchResult = {
                id: ids[i],
                distance: results.distances[0][i],
                metadata: results.metadatas[0][i],
                document: results.documents[0][i]
            };
            const resultItem = createSearchResultElement(searchResult);
            meetingsList.appendChild(resultItem);
        }
    };

    // --- Element Creation ---
    const createMeetingElement = (meeting) => {
        const item = document.createElement('li');
        item.className = 'meeting-item';
        const header = document.createElement('div');
        header.className = 'meeting-header';
        header.innerHTML = `<h2>${meeting.title}</h2><div class="date">${new Date(meeting.date).toLocaleString()}</div>`;

        const content = document.createElement('div');
        content.className = 'meeting-content';
        content.innerHTML = `<h3>Summary</h3><p>${meeting.summary || 'N/A'}</p><h3>Full Transcript</h3><pre>${meeting.full_transcript || 'N/A'}</pre>`;

        item.appendChild(header);
        item.appendChild(content);

        header.addEventListener('click', () => content.classList.toggle('visible'));
        return item;
    };

    const createSearchResultElement = (result) => {
        const item = document.createElement('li');
        item.className = 'meeting-item';
        const header = document.createElement('div');
        header.className = 'meeting-header';
        header.innerHTML = `<h2>${result.metadata.meeting_id}</h2><div class="date">Similarity: ${(1 - result.distance).toFixed(2)}</div>`;

        const content = document.createElement('div');
        content.className = 'meeting-content visible'; // Show by default for search results
        content.innerHTML = `<p>"...${result.document}..."</p><p><em>(Time: ${result.metadata.start} - ${result.metadata.end})</em></p>`;

        item.appendChild(header);
        item.appendChild(content);
        return item;
    };

    // --- UI Helpers ---
    const clearResults = () => {
        meetingsList.innerHTML = '';
        resultsHeader.innerHTML = '';
    };

    const addClearSearchButton = () => {
        const button = document.createElement('button');
        button.textContent = 'Clear Search & Show All Meetings';
        button.onclick = fetchAndRenderMeetings;
        resultsHeader.appendChild(document.createElement('br'));
        resultsHeader.appendChild(button);
    };

    // --- Event Listeners ---
    searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const query = searchInput.value.trim();
        if (query) {
            performSearch(query);
        }
    });

    // --- Initial Load ---
    fetchAndRenderMeetings();
});
