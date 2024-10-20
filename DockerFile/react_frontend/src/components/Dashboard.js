import React, { useState, useEffect } from 'react';
import './Dashboard.css';

const socketUrl = 'ws://localhost:5001';

const Dashboard = () => {
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let socket;

        const connectWebSocket = () => {
            socket = new WebSocket(socketUrl);

            socket.onopen = () => {
                console.log('WebSocket connected');
            };

            socket.onmessage = (event) => {
                const data = JSON.parse(event.data);

                if (data.type === 'initialMessages') {
                    setMessages(data.data);
                    setLoading(false);
                } else if (data.type === 'newMessage') {
                    // Ensure the new message is fully parsed and valid
                    const newMessage = {
                        time: data.data.time || 'N/A',
                        job_id: data.data.job_id || 'N/A',
                        content_id: data.data.content_id || 'N/A',
                        content_type: data.data.content_type || 'N/A',
                        file_name: data.data.file_name || 'N/A',
                        status: data.data.status || 'N/A',
                        message: data.data.message || 'N/A',
                    };
                    setMessages((prevMessages) => [newMessage, ...prevMessages]);
                }
            };

            socket.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

            socket.onclose = () => {
                console.log('WebSocket disconnected. Reconnecting...');
                setTimeout(() => {
                    connectWebSocket();
                }, 3000);
            };
        };

        connectWebSocket();

        return () => {
            if (socket) {
                socket.close();
            }
        };
    }, []);

    const renderMessages = () => {
        if (loading) {
            return (
                <tr>
                    <td colSpan="7" className="loading">Loading messages...</td>
                </tr>
            );
        }

        if (messages.length === 0) {
            return (
                <tr>
                    <td colSpan="7" className="no-messages">No messages found</td>
                </tr>
            );
        }

        return messages.map((msg, index) => (
            <tr key={index}>
                <td>{msg.time}</td>
                <td>{msg.job_id}</td>
                <td>{msg.content_id}</td>
                <td>{msg.content_type}</td>
                <td>{msg.file_name}</td>
                <td>{msg.status}</td>
                <td>{msg.message}</td>
            </tr>
        ));
    };

    return (
        <div className="dashboard-container">
            <div className="dashboard-header">Message Dashboard</div>
            <div className="table-container">
                <table className="dashboard-table">
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>JobID</th>
                            <th>ContentID</th>
                            <th>ContentType</th>
                            <th>FileName</th>
                            <th>Status</th>
                            <th>Message</th>
                        </tr>
                    </thead>
                    <tbody>
                        {renderMessages()}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default Dashboard;
