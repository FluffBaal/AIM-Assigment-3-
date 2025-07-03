import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { HomePage } from './pages/HomePage';
import { ChatPage } from './pages/ChatPage';
import { ApiKeyProvider } from './contexts/ApiKeyContext';

function App() {
  return (
    <ApiKeyProvider>
      <Router>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<HomePage />} />
            <Route path="chat/:fileId" element={<ChatPage />} />
          </Route>
        </Routes>
      </Router>
    </ApiKeyProvider>
  );
}

export default App;
