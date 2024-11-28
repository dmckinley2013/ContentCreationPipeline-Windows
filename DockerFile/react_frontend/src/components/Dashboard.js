import React, { useState, useEffect, useRef } from 'react';
import './Dashboard.css';

const Dashboard = () => {
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isConnected, setIsConnected] = useState(false);
    const ws = useRef(null);
    const [truncatedContentIds, setTruncatedContentIds] = useState({});


    const [expandedContentIds, setExpandedContentIds] = useState([]);

    const [searchTerm, setSearchTerm] = useState('');
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage, setItemsPerPage] = useState(10);
    const [selectedContentType, setSelectedContentType] = useState('All');

    // Helper function to truncate IDs
    const truncateId = (id) => {
        if (!id) return '';
        return id.length > 10 ? `...${id.slice(-10)}` : id;
    };

    const normalizeContentType = (type) => {
        return type === 'Picture' ? 'Image' : type;
    };

    // Group messages by content_id
    const groupedMessages = messages.reduce((acc, msg) => {
        const contentId = msg.content_id;
        if (!acc[contentId]) {
            acc[contentId] = [];
        }
        acc[contentId].push(msg);
        return acc;
    }, {});

    // Sort content groups by the latest timestamp
    const sortedGroupedMessages = Object.entries(groupedMessages).sort((a, b) => {
        const getLastTimestamp = (msgs) => {
            return Math.max(...msgs.map(msg => new Date(msg.time).getTime() || 0));
        };
        return getLastTimestamp(b[1]) - getLastTimestamp(a[1]);
    });

    // Filter messages based on search term and content type
    const filteredContent = sortedGroupedMessages.filter(([contentId, msgs]) => {
        const matchesSearch = contentId.toLowerCase().includes(searchTerm.toLowerCase()) ||
            msgs.some(msg => Object.values(msg).some(value =>
                value?.toString().toLowerCase().includes(searchTerm.toLowerCase())
            ));
        
        const matchesContentType = selectedContentType === 'All' ||
            msgs.some(msg => normalizeContentType(msg.content_type) === selectedContentType);
        
        return matchesSearch && matchesContentType;
    });

    // Pagination calculations
    const indexOfLastContent = currentPage * itemsPerPage;
    const indexOfFirstContent = indexOfLastContent - itemsPerPage;
    const currentContent = filteredContent.slice(indexOfFirstContent, indexOfLastContent);
    const totalPages = Math.ceil(filteredContent.length / itemsPerPage);

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
                        setMessages([...data.data]);
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

    const toggleExpandContentId = (contentId) => {
        setExpandedContentIds((prevExpanded) =>
            prevExpanded.includes(contentId)
                ? prevExpanded.filter((id) => id !== contentId)
                : [...prevExpanded, contentId]
        );
    };
    
    
    //     // Truncate the contentId and store it in state
    //     setTruncatedContentIds((prevTruncated) => ({
    //         ...prevTruncated,
    //         [contentId]: contentId.includes('.') ? contentId.split('.')[0] : contentId,
    //     }));
    // };
    

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
                                placeholder="Search by Content ID, Job ID, etc..."
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
                                <option value={10}>10 Items per page</option>
                                <option value={25}>25 Items per page</option>
                                <option value={50}>50 Items per page</option>
                            </select>
                        </div>
                    </div>

                    <div className="table-wrapper">
                        <table className="dashboard-table">
                            <thead>
                                <tr>
                                    <th>Content ID</th>
                                    <th>Job ID</th>
                                    <th>Time</th>
                                    <th>Content Type</th>
                                    <th>File Name</th>
                                    <th> Media ID</th>
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
    ) : currentContent.length > 0 ? (
        currentContent.map(([contentId, msgs]) => (
            <React.Fragment key={contentId}>
                {/* Main row for Content ID */}
                <tr 
                    className="content-row" 
                    onClick={() => toggleExpandContentId(contentId)}
                 >
                    {/* <td>{expandedContentIds.includes(contentId) ? (contentId.includes('.') ? contentId.split('.')[0] : contentId) : contentId}</td> */}
                    <td>{expandedContentIds.includes(contentId) ?  contentId : contentId}</td>
                    <td colSpan="6" className="id-cell">
                        {expandedContentIds.includes(contentId) ? '▼' : '▶'}
                    </td>
                </tr>

                {/* Expanded content rows */}
                {expandedContentIds.includes(contentId) && (
                    <tr className="expanded-row">
                        <td colSpan="7">
                            <table className="expanded-table">
                                <thead>
                                    <tr>
                                        <th>Job ID</th>
                                        <th>Time</th>
                                        <th>Content Type</th>
                                        <th>File Name</th>
                                        <th>Media ID</th>
                                        <th>Status</th>
                                        <th>Message</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {msgs.map((msg, index) => (
                                        <tr key={`${msg.job_id}-${index}`}>
                                            <td>{truncateId(msg.job_id)}</td>
                                            <td>{msg.time}</td>
                                            <td>
                                                <span className={`content-type ${normalizeContentType(msg.content_type).toLowerCase()}`}>
                                                    {normalizeContentType(msg.content_type)}
                                                </span>
                                            </td>
                                            <td>{msg.file_name}</td>
                                            <td>{truncateId(msg.media_id)}</td>
                                            <td>
                                                <span className={`status ${msg.status.toLowerCase()}`}>
                                                    {msg.status}
                                                </span>
                                            </td>
                                            <td>{msg.message}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </td>
                    </tr>
                )}
            </React.Fragment>
        ))
    ) : (
        <tr>
            <td colSpan="7">No content found</td>
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
