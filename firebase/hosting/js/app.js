document.addEventListener('DOMContentLoaded', () => {
    // --- Firebase Configuration ---
    // IMPORTANT: Replace with your project's Firebase configuration object.
    // You can find this in your Firebase project settings.
    const firebaseConfig = {
        apiKey: "YOUR_API_KEY",
        authDomain: "YOUR_AUTH_DOMAIN",
        projectId: "YOUR_PROJECT_ID",
        storageBucket: "YOUR_STORAGE_BUCKET",
        messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
        appId: "YOUR_APP_ID"
    };

    // --- Initialize Firebase and Firestore ---
    try {
        firebase.initializeApp(firebaseConfig);
    } catch (e) {
        console.error('Error initializing Firebase:', e);
        document.getElementById('loader').textContent = 'Error: Could not initialize Firebase. Please check your configuration.';
        return;
    }

    const db = firebase.firestore();
    const meetingsList = document.getElementById('meetings-list');
    const loader = document.getElementById('loader');

    // --- PWA: Register Service Worker ---
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                console.log('Service Worker registered with scope:', registration.scope);
            })
            .catch(error => {
                console.error('Service Worker registration failed:', error);
            });
    }

    // --- Fetch and Render Meetings ---
    const fetchMeetings = async () => {
        try {
            const snapshot = await db.collection('meetings').orderBy('date', 'desc').get();

            if (snapshot.empty) {
                loader.textContent = 'No meetings found.';
                return;
            }

            loader.style.display = 'none';

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

    // --- Create HTML Element for a single meeting ---
    const createMeetingElement = (meeting) => {
        const item = document.createElement('li');
        item.className = 'meeting-item';
        item.setAttribute('data-id', meeting.meeting_id);

        const header = document.createElement('div');
        header.className = 'meeting-header';

        const title = document.createElement('h2');
        title.textContent = meeting.title;

        const date = document.createElement('div');
        date.className = 'date';
        date.textContent = new Date(meeting.date).toLocaleString();

        header.appendChild(title);
        header.appendChild(date);

        const content = document.createElement('div');
        content.className = 'meeting-content';

        const summaryHeader = document.createElement('h3');
        summaryHeader.textContent = 'Summary';
        const summaryText = document.createElement('p');
        summaryText.textContent = meeting.summary || 'No summary available.';

        const transcriptHeader = document.createElement('h3');
        transcriptHeader.textContent = 'Full Transcript';
        const transcriptText = document.createElement('pre');
        transcriptText.textContent = meeting.full_transcript || 'No transcript available.';

        content.appendChild(summaryHeader);
        content.appendChild(summaryText);
        content.appendChild(transcriptHeader);
        content.appendChild(transcriptText);

        item.appendChild(header);
        item.appendChild(content);

        // Add click listener to toggle content visibility
        header.addEventListener('click', () => {
            content.classList.toggle('visible');
        });

        return item;
    };

    // --- Initial Load ---
    fetchMeetings();
});
