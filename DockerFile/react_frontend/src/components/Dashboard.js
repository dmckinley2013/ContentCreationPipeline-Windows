import React, { useState, useEffect, useRef } from 'react';
import './Dashboard.css';

const Dashboard = () => {
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isConnected, setIsConnected] = useState(false);
    const ws = useRef(null);

    // New state variables for filtering, search, and pagination
    const [searchTerm, setSearchTerm] = useState('');
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage, setItemsPerPage] = useState(10);
    const [selectedContentType, setSelectedContentType] = useState('All');

    // Helper function to truncate IDs and show last 10 characters
    const truncateId = (id) => {
        if (!id) return '';
        return id.length > 10 ? `...${id.slice(-10)}` : id;
    };

    // Helper function to normalize content type
    const normalizeContentType = (type) => {
        return type === 'Picture' ? 'Image' : type;
    };

    // Filter messages based on search term and content type
    const filteredMessages = messages.filter(msg => {
        const matchesSearch = Object.values(msg).some(value => 
            value?.toString().toLowerCase().includes(searchTerm.toLowerCase())
        );
        const matchesContentType = selectedContentType === 'All' || 
            normalizeContentType(msg.content_type) === selectedContentType;
        
        return matchesSearch && matchesContentType;
    });

    // Pagination calculations
    const indexOfLastMessage = currentPage * itemsPerPage;
    const indexOfFirstMessage = indexOfLastMessage - itemsPerPage;
    const currentMessages = filteredMessages.slice(indexOfFirstMessage, indexOfLastMessage);
    const totalPages = Math.ceil(filteredMessages.length / itemsPerPage);

    // Reset to first page when search or filter changes
    useEffect(() => {
        setCurrentPage(1);
    }, [searchTerm, selectedContentType, itemsPerPage]);

    const formatTime = (timeString) => {
        if (!timeString) return 'No date';
        
        try {
            let date = new Date(timeString);
            
            if (isNaN(date.getTime())) {
                const parts = timeString.match(/(\d{1,2})\/(\d{1,2})\/(\d{4}), (\d{1,2}):(\d{2}):(\d{2}) ([AP]M)/);
                if (parts) {
                    const [_, month, day, year, hours, minutes, seconds, ampm] = parts;
                    let hour = parseInt(hours);
                    if (ampm === 'PM' && hour < 12) hour += 12;
                    if (ampm === 'AM' && hour === 12) hour = 0;
                    date = new Date(year, month - 1, day, hour, parseInt(minutes), parseInt(seconds));
                }
            }

            if (isNaN(date.getTime())) {
                return 'No date';
            }

            const formatter = new Intl.DateTimeFormat('en-US', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: true,
            });

            return formatter.format(date).replace(',', ', ');

        } catch (error) {
            console.error('Date parsing error:', error, 'for timestamp:', timeString);
            return 'No date';
        }
    };

    useEffect(() => {
        const connectWebSocket = () => {
            ws.current = new WebSocket('ws://localhost:5001');

            ws.current.onopen = () => {
                console.log('WebSocket connected');
                setIsConnected(true);
            };

            ws.current.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log('WebSocket data received:', data);

                    if (data.type === 'initialMessages') {
                        setMessages(prevMessages => {
                            const sortedMessages = [...data.data].sort((a, b) => {
                                try {
                                    const dateA = new Date(a.time || 0);
                                    const dateB = new Date(b.time || 0);
                                    
                                    if (isNaN(dateA.getTime()) || isNaN(dateB.getTime())) {
                                        const parseSpecificFormat = (timeStr) => {
                                            if (!timeStr) return new Date(0);
                                            const parts = timeStr.match(/(\d{1,2})\/(\d{1,2})\/(\d{4}), (\d{1,2}):(\d{2}):(\d{2}) ([AP]M)/);
                                            if (!parts) return new Date(0);
                                            const [_, month, day, year, hours, minutes, seconds, ampm] = parts;
                                            let hour = parseInt(hours);
                                            if (ampm === 'PM' && hour < 12) hour += 12;
                                            if (ampm === 'AM' && hour === 12) hour = 0;
                                            return new Date(year, month - 1, day, hour, parseInt(minutes), parseInt(seconds));
                                        };
                                        return parseSpecificFormat(b.time) - parseSpecificFormat(a.time);
                                    }
                                    return dateB - dateA;
                                } catch (error) {
                                    console.error('Sorting error:', error);
                                    return 0;
                                }
                            });
                            return sortedMessages;
                        });
                        setLoading(false);
                    } else if (data.type === 'newMessage') {
                        setMessages(prevMessages => [data.data, ...prevMessages]);
                    }
                } catch (err) {
                    console.error('Failed to parse WebSocket message:', err);
                }
            };

            ws.current.onerror = (error) => {
                console.error('WebSocket error:', error);
                setIsConnected(false);
            };

            ws.current.onclose = () => {
                console.log('WebSocket disconnected');
                setIsConnected(false);
                setTimeout(connectWebSocket, 3000);
            };
        };

        connectWebSocket();

        return () => {
            if (ws.current) {
                ws.current.close();
            }
        };
    }, []);
    return (
        <div className="dashboard-wrapper">
            <header className="dashboard-header">
                <div className="header-content">
                    <img 
                        src="/NETC.jpg"
                        alt="NETC Logo" 
                        className="netc-logo"
                    />
                    <div className="header-text">
                        <h1>Message Processing Dashboard</h1>
                        <p className="subtitle">Real-time File Processing Monitor</p>
                    </div>
                    <div className="connection-status">
                        <div className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
                            {isConnected ? 'Connected' : 'Connecting...'}
                        </div>
                    </div>
                </div>
            </header>

            <main className="dashboard-main">
                <div className="stats-section">
                    <div className="stat-card">
                        <h3>Total Messages</h3>
                        <p className="stat-number">{messages.length}</p>
                    </div>
                    <div className="stat-card">
                        <h3>Documents</h3>
                        <p className="stat-number">
                            {messages.filter(m => m.content_type === 'Document').length}
                        </p>
                    </div>
                    <div className="stat-card">
                        <h3>Images</h3>
                        <p className="stat-number">
                            {messages.filter(m => m.content_type === 'Image' || m.content_type === 'Picture').length}
                        </p>
                    </div>
                    <div className="stat-card">
                        <h3>Audio Files</h3>
                        <p className="stat-number">
                            {messages.filter(m => m.content_type === 'Audio').length}
                        </p>
                    </div>
                </div>

                <div className="table-container">
                    <div className="table-controls">
                        <div className="search-bar">
                            <input
                                type="text"
                                placeholder="Search all fields..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="search-input"
                            />
                        </div>
                        <div className="filter-controls">
                            <select
                                value={selectedContentType}
                                onChange={(e) => setSelectedContentType(e.target.value)}
                                className="filter-select"
                            >
                                <option value="All">All Types</option>
                                <option value="Document">Document</option>
                                <option value="Image">Image</option>
                                <option value="Audio">Audio</option>
                            </select>
                            <select
                                value={itemsPerPage}
                                onChange={(e) => setItemsPerPage(Number(e.target.value))}
                                className="page-size-select"
                            >
                                <option value={10}>10 per page</option>
                                <option value={25}>25 per page</option>
                                <option value={50}>50 per page</option>
                            </select>
                        </div>
                    </div>

                    <div className="table-wrapper">
                        <table className="dashboard-table">
                            <thead>
                                <tr>
                                    <th>Time</th>
                                    <th>Job ID</th>
                                    <th>Content ID</th>
                                    <th>Content Type</th>
                                    <th>File Name</th>
                                    <th>Status</th>
                                    <th>Message</th>
                                </tr>
                            </thead>
                            <tbody>
                                {loading ? (
                                    <tr>
                                        <td colSpan="7">
                                            <div className="loading-spinner">
                                                <div className="spinner"></div>
                                                <p>Loading messages...</p>
                                            </div>
                                        </td>
                                    </tr>
                                ) : currentMessages.length > 0 ? (
                                    currentMessages.map((msg, index) => (
                                        <tr key={`${msg.job_id}-${msg.content_id}-${index}`}>
                                            <td>{msg.time}</td>
                                            <td title={msg.job_id} className="id-cell">
                                                {truncateId(msg.job_id)}
                                            </td>
                                            <td title={msg.content_id} className="id-cell">
                                                {truncateId(msg.content_id)}
                                            </td>
                                            <td>
                                                <span className={`content-type ${normalizeContentType(msg.content_type).toLowerCase()}`}>
                                                    {normalizeContentType(msg.content_type)}
                                                </span>
                                            </td>
                                            <td>{msg.file_name}</td>
                                            <td>
                                                <span className={`status ${msg.status.toLowerCase()}`}>
                                                    {msg.status}
                                                </span>
                                            </td>
                                            <td>{msg.message}</td>
                                        </tr>
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan="7">No messages found</td>
                                    </tr>
                                )}
                            </tbody>
                        </table>

                        <div className="pagination">
                            <button 
                                onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                                disabled={currentPage === 1}
                                className="page-button"
                            >
                                Previous
                            </button>
                            <span className="page-info">
                                Page {currentPage} of {totalPages || 1}
                            </span>
                            <button 
                                onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                                disabled={currentPage === totalPages || totalPages === 0}
                                className="page-button"
                            >
                                Next
                            </button>
                        </div>
                    </div>
                </div>
            </main>

            <footer className="dashboard-footer">
                <p>© 2024 NETC. All rights reserved.</p>
            </footer>
        </div>
    );
};

export default Dashboard;