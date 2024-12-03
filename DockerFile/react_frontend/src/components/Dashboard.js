import React, { useState, useEffect, useRef } from 'react';
import './Dashboard.css';
import Button from '@mui/material/Button';
import { CircularProgress } from '@mui/material';
import { ExpandMore, ExpandLess } from '@mui/icons-material';
import { ThemeProvider, createTheme } from '@mui/material/styles';

// Custom theme for Material-UI
const theme = createTheme({
  palette: {
    primary: {
      main: '#1a237e',
    },
    secondary: {
      main: '#0d47a1',
    },
  },
  typography: {
    fontFamily: 'Roboto, sans-serif',
  },
});

// Create MetricCard component
const MetricCard = ({ title, value }) => (
  <div className="metric-card">
    <h4>{title}</h4>
    <p>{value}</p>
  </div>
);

const Dashboard = () => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isConnected, setIsConnected] = useState(false);
  const ws = useRef();
  const [expandedContentIds, setExpandedContentIds] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [selectedContentType, setSelectedContentType] = useState('All');
  const [showAnalytics, setShowAnalytics] = useState(false);

  const [performanceStats, setPerformanceStats] = useState({
    averageResponseTime: 0,
    cpuUtilization: 0,
    memoryUsage: 0,
    currentLoad: 0,
    uptime: 0,
    networkStats: {
      bytesSent: 0,
      bytesReceived: 0,
      activeConnections: 0,
      messageRate: 0,
    },
  });

  const [fileStats, setFileStats] = useState({
    totalFilesProcessed: 0,
    fileTypeDistribution: {
      Document: 0,
      Image: 0,
      Audio: 0,
    },
  });

  const [systemHealth, setSystemHealth] = useState({
    activeConnections: isConnected ? 1 : 0,
    queueDepth: 0,
    memoryUsage: 0,
    successRate: 100,
  });

  const requestAnalytics = () => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: 'getAnalytics' }));
    }
  };

  const handleAnalyticsClick = () => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: 'getAnalytics' }));
    }
    setShowAnalytics(!showAnalytics);
  };

  useEffect(() => {
    if (showAnalytics) {
      requestAnalytics();
      const interval = setInterval(requestAnalytics, 5000);
      return () => clearInterval(interval);
    }
  }, [showAnalytics]);

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
            setMessages((prevMessages) => [data.data, ...prevMessages]);
          } else if (data.type === 'analytics') {
            setPerformanceStats((prevStats) => ({
              ...prevStats,
              ...data.data.performanceStats,
            }));
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

  const truncateId = (id) => {
    if (!id) return '';
    return id.length > 10 ? `${id.slice(0, 5)}...${id.slice(-5)}` : id;
  };

  // Function to sanitize class names
  const sanitizeClassName = (text) => {
    return text?.toLowerCase().replace(/\s+/g, '-').replace(/[^\w-]/g, '');
  };

  // Update fileStats and systemHealth whenever messages change
  useEffect(() => {
    const totalMessages = messages.length;
    const documentMessages = messages.filter((m) => m.content_type === 'Document').length;
    const imageMessages = messages.filter((m) => m.content_type === 'Image' || m.content_type === 'Picture').length;
    const audioMessages = messages.filter((m) => m.content_type === 'Audio').length;

    setFileStats({
      totalFilesProcessed: totalMessages,
      fileTypeDistribution: {
        Document: documentMessages,
        Image: imageMessages,
        Audio: audioMessages,
      },
    });

    const queuedMessages = messages.filter((m) => m.status === 'Queued').length;
    const processedMessages = messages.filter((m) => m.status === 'Processed').length;
    const successRate = totalMessages > 0 ? (processedMessages / totalMessages) * 100 : 100;

    setSystemHealth({
      activeConnections: isConnected ? 1 : 0,
      queueDepth: queuedMessages,
      memoryUsage: (totalMessages * 1024) / (1024 * 1024), // Rough estimate in MB
      successRate: successRate,
    });
  }, [messages, isConnected]);

  const groupedMessages = messages.reduce((acc, msg) => {
    const contentId = msg.content_id;
    if (!acc[contentId]) {
      acc[contentId] = [];
    }
    acc[contentId].push(msg);
    return acc;
  }, {});

  const sortedGroupedMessages = Object.entries(groupedMessages).sort(
    (a, b) => {
      const getLastTimestamp = (msgs) => {
        return Math.max(
          ...msgs.map((msg) => new Date(msg.time).getTime() || 0)
        );
      };
      return getLastTimestamp(b[1]) - getLastTimestamp(a[1]);
    }
  );

  const filteredContent = sortedGroupedMessages.filter(([contentId, msgs]) => {
    const matchesSearch =
      contentId.toLowerCase().includes(searchTerm.toLowerCase()) ||
      msgs.some((msg) =>
        Object.values(msg).some((value) =>
          value?.toString().toLowerCase().includes(searchTerm.toLowerCase())
        )
      );

    const matchesContentType =
      selectedContentType === 'All' ||
      msgs.some((msg) => msg.content_type === selectedContentType);

    return matchesSearch && matchesContentType;
  });

  const indexOfLastContent = currentPage * itemsPerPage;
  const indexOfFirstContent = indexOfLastContent - itemsPerPage;
  const currentContent = filteredContent.slice(
    indexOfFirstContent,
    indexOfLastContent
  );
  const totalPages = Math.ceil(filteredContent.length / itemsPerPage);

  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, selectedContentType, itemsPerPage]);

  return (
    <ThemeProvider theme={theme}>
      <div className="dashboard-wrapper">
        <header className="dashboard-header">
          <div className="header-content">
            <img src="/NETC.jpg" alt="NETC Logo" className="netc-logo" />
            <div className="header-text">
              <h1>Message Processing Dashboard</h1>
              <p className="subtitle">Real-time File Processing Monitor</p>
            </div>
            <div className="connection-status">
              <div
                className={`status-indicator ${
                  isConnected ? 'connected' : 'disconnected'
                }`}
              >
                {isConnected ? 'Connected' : 'Connecting...'}
              </div>
            </div>
          </div>
        </header>

        <main className="dashboard-main">
          <div className="stats-section">
            <div className="stat-card">
              <h3>Total Messages</h3>
              <p className="stat-number">{fileStats.totalFilesProcessed}</p>
            </div>
            <div className="stat-card">
              <h3>Documents</h3>
              <p className="stat-number">
                {fileStats.fileTypeDistribution.Document}
              </p>
            </div>
            <div className="stat-card">
              <h3>Images</h3>
              <p className="stat-number">
                {fileStats.fileTypeDistribution.Image}
              </p>
            </div>
            <div className="stat-card">
              <h3>Audio Files</h3>
              <p className="stat-number">
                {fileStats.fileTypeDistribution.Audio}
              </p>
            </div>
          </div>

          {/* Removed the Pie Chart section */}

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
                    <th>Media ID</th>
                    <th>Status</th>
                    <th>Message</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr>
                      <td colSpan="8">
                        <div className="loading-spinner">
                          <CircularProgress />
                          <p>Loading messages...</p>
                        </div>
                      </td>
                    </tr>
                  ) : currentContent.length > 0 ? (
                    currentContent.map(([contentId, msgs]) => (
                      <React.Fragment key={contentId}>
                        <tr
                          className="content-row"
                          onClick={() => toggleExpandContentId(contentId)}
                        >
                          <td className="id-cell" title={contentId}>
                            {expandedContentIds.includes(contentId)
                              ? contentId
                              : truncateId(contentId)}
                          </td>
                          <td colSpan="7" className="expand-cell">
                            {expandedContentIds.includes(contentId) ? (
                              <ExpandLess />
                            ) : (
                              <ExpandMore />
                            )}
                          </td>
                        </tr>

                        {expandedContentIds.includes(contentId) && (
                          <tr className="expanded-row">
                            <td colSpan="8">
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
                                      <td
                                        className="id-cell"
                                        title={msg.job_id}
                                      >
                                        {truncateId(msg.job_id)}
                                      </td>
                                      <td>{msg.time}</td>
                                      <td>
                                        <span
                                          className={`content-type ${sanitizeClassName(
                                            msg.content_type
                                          )}`}
                                          title={msg.content_type}
                                        >
                                          {msg.content_type}
                                        </span>
                                      </td>
                                      <td>{msg.file_name}</td>
                                      <td
                                        className="id-cell"
                                        title={msg.media_id}
                                      >
                                        {truncateId(msg.media_id)}
                                      </td>
                                      <td>
                                        <span
                                          className={`status ${sanitizeClassName(
                                            msg.status
                                          )}`}
                                          title={msg.status}
                                        >
                                          {msg.status}
                                        </span>
                                      </td>
                                      <td
                                        className={`message ${sanitizeClassName(
                                          msg.status
                                        )}`}
                                      >
                                        {msg.message}
                                      </td>
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
                      <td colSpan="8">No content found</td>
                    </tr>
                  )}
                </tbody>
              </table>

              <div className="pagination">
                <Button
                  variant="contained"
                  color="primary"
                  onClick={() =>
                    setCurrentPage((prev) => Math.max(prev - 1, 1))
                  }
                  disabled={currentPage === 1}
                  className="page-button"
                >
                  Previous
                </Button>
                <span className="page-info">
                  Page {currentPage} of {totalPages || 1}
                </span>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={() =>
                    setCurrentPage((prev) => Math.min(prev + 1, totalPages))
                  }
                  disabled={currentPage === totalPages || totalPages === 0}
                  className="page-button"
                >
                  Next
                </Button>
              </div>
            </div>

            <Button
              variant="contained"
              color="secondary"
              onClick={handleAnalyticsClick}
              className="analytics-button"
            >
              {showAnalytics ? 'Hide Analytics' : 'View Analytics'}
            </Button>

            {showAnalytics && (
              <div className="analytics-panel">
                <div className="analytics-section">
                  <h3>System Performance</h3>
                  <div className="metrics-grid">
                    <MetricCard
                      title="CPU Usage"
                      value={`${performanceStats.cpuUtilization}%`}
                    />
                    <MetricCard
                      title="Memory Usage"
                      value={`${performanceStats.memoryUsage}%`}
                    />
                    <MetricCard
                      title="System Load"
                      value={performanceStats.currentLoad}
                    />
                    <MetricCard
                      title="Uptime"
                      value={`${Math.floor(
                        performanceStats.uptime / 3600
                      )}h ${Math.floor(
                        (performanceStats.uptime % 3600) / 60
                      )}m`}
                    />
                  </div>
                </div>

                <div className="analytics-section">
                  <h3>Network Performance</h3>
                  <div className="metrics-grid">
                    <MetricCard
                      title="Data Sent"
                      value={`${(
                        (performanceStats?.networkStats?.bytesSent || 0) /
                        1024 /
                        1024
                      ).toFixed(2)} MB`}
                    />
                    <MetricCard
                      title="Data Received"
                      value={`${(
                        (performanceStats?.networkStats?.bytesReceived || 0) /
                        1024 /
                        1024
                      ).toFixed(2)} MB`}
                    />
                    <MetricCard
                      title="Active Connections"
                      value={
                        performanceStats?.networkStats?.activeConnections || 0
                      }
                    />
                    <MetricCard
                      title="Messages/sec"
                      value={(
                        performanceStats?.networkStats?.messageRate || 0
                      ).toFixed(2)}
                    />
                  </div>
                </div>

                <div className="analytics-section">
                  <h3>Processing Statistics</h3>
                  <div className="metrics-grid">
                    <MetricCard
                      title="Total Files"
                      value={fileStats.totalFilesProcessed}
                    />
                    <MetricCard
                      title="Success Rate"
                      value={`${systemHealth.successRate.toFixed(1)}%`}
                    />
                    <MetricCard
                      title="Queue Depth"
                      value={systemHealth.queueDepth}
                    />
                    <MetricCard
                      title="Avg Response Time"
                      value={`${performanceStats.averageResponseTime.toFixed(
                        0
                      )}ms`}
                    />
                  </div>
                </div>
              </div>
            )}
          </div>

          <footer className="dashboard-footer">
            <p>© 2024 NETC. All rights reserved.</p>
          </footer>
        </main>
      </div>
    </ThemeProvider>
  );
};

export default Dashboard;
