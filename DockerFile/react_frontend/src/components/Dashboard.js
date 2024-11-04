import React, { useState, useEffect, useRef } from 'react';
import './Dashboard.css';

const Dashboard = () => {
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isConnected, setIsConnected] = useState(false);
    const ws = useRef(null);

    const [expandedJobIds, setExpandedJobIds] = useState([]);

    const [searchTerm, setSearchTerm] = useState('');
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage, setItemsPerPage] = useState(10);
    const [selectedContentType, setSelectedContentType] = useState('All');

    // Helper function to truncate Content IDs
    const truncateId = (id) => {
        if (!id) return '';
        return id.length > 10 ? `...${id.slice(-10)}` : id;
    };

    const normalizeContentType = (type) => {
        return type === 'Picture' ? 'Image' : type;
    };

    const groupedMessages = messages.reduce((acc, msg) => {
        const jobId = msg.job_id;
        if (!acc[jobId]) {
            acc[jobId] = [];
        }
        acc[jobId].push(msg);
        return acc;
    }, {});

    // Sort jobs by the latest timestamp in their content
    const sortedGroupedMessages = Object.entries(groupedMessages).sort((a, b) => {
        const getLastTimestamp = (msgs) => {
            return Math.max(...msgs.map(msg => new Date(msg.time).getTime() || 0));
        };
        return getLastTimestamp(b[1]) - getLastTimestamp(a[1]);
    });

    // Filter messages based on search term and content type
    const filteredJobs = sortedGroupedMessages.filter(([jobId, msgs]) => {
        const matchesSearch = jobId.toLowerCase().includes(searchTerm.toLowerCase()) ||
            msgs.some(msg => Object.values(msg).some(value => 
                value?.toString().toLowerCase().includes(searchTerm.toLowerCase())
            ));
        
        const matchesContentType = selectedContentType === 'All' ||
            msgs.some(msg => normalizeContentType(msg.content_type) === selectedContentType);
        
        return matchesSearch && matchesContentType;
    });

    // Pagination calculations based on job_id
    const indexOfLastJob = currentPage * itemsPerPage;
    const indexOfFirstJob = indexOfLastJob - itemsPerPage;
    const currentJobs = filteredJobs.slice(indexOfFirstJob, indexOfLastJob);
    const totalPages = Math.ceil(filteredJobs.length / itemsPerPage);

    useEffect(() => {
        setCurrentPage(1);
    }, [searchTerm, selectedContentType, itemsPerPage]);

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
                        setMessages(prevMessages => [...data.data]);
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

    const toggleExpandJobId = (jobId) => {
        setExpandedJobIds((prevExpanded) => 
            prevExpanded.includes(jobId) ? prevExpanded.filter(id => id !== jobId) : [...prevExpanded, jobId]
        );
    };

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
                                placeholder="Search by Job ID, Content ID, etc..."
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
                                <option value={10}>10 Jobs per page</option>
                                <option value={25}>25 Jobs per page</option>
                                <option value={50}>50 Jobs per page</option>
                            </select>
                        </div>
                    </div>

                    <div className="table-wrapper">
                        <table className="dashboard-table">
                            <thead>
                                <tr>
                                    <th>Job ID</th>
                                    <th>Time</th>
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
                                ) : currentJobs.length > 0 ? (
                                    currentJobs.map(([jobId, msgs]) => (
                                        <React.Fragment key={jobId}>
                                            <tr 
                                                className="job-row" 
                                                onClick={() => toggleExpandJobId(jobId)}
                                            >
                                                <td>{jobId}</td>
                                                <td colSpan="6" className="expand-cell">
                                                    {expandedJobIds.includes(jobId) ? '▼' : '▶'}
                                                </td>
                                            </tr>
                                            {expandedJobIds.includes(jobId) && msgs.map((msg, index) => (
                                                <tr key={`${msg.content_id}-${index}`} className="content-row">
                                                    <td></td>
                                                    <td>{msg.time}</td>
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
                                            ))}
                                        </React.Fragment>
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan="7">No jobs found</td>
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
