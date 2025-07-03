# RAG Chat Application User Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Setting Up Your API Key](#setting-up-your-api-key)
3. [Uploading PDFs](#uploading-pdfs)
4. [Chatting with Your Documents](#chatting-with-your-documents)
5. [Understanding Sources](#understanding-sources)
6. [Tips and Best Practices](#tips-and-best-practices)
7. [Troubleshooting](#troubleshooting)
8. [FAQ](#faq)

## Getting Started

The RAG Chat Application allows you to upload PDF documents and have intelligent conversations about their content using advanced language models. The application uses Retrieval-Augmented Generation (RAG) to provide accurate, context-aware responses based on your documents.

### What You'll Need

1. **OpenAI API Key**: You'll need your own OpenAI API key to use the application
2. **PDF Documents**: Any PDF files you want to analyze (up to 10MB each)
3. **Modern Web Browser**: Chrome, Firefox, Safari, or Edge (latest versions)

## Setting Up Your API Key

### First Time Setup

1. When you first visit the application, you'll see a modal asking for your OpenAI API key
2. Enter your API key (it should start with `sk-`)
3. Click "Submit"

### Getting an OpenAI API Key

1. Visit [platform.openai.com](https://platform.openai.com)
2. Sign up or log in to your account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (you won't be able to see it again!)

### API Key Security

- Your API key is stored locally in your browser
- It's never sent to our servers
- It's only used to communicate directly with OpenAI
- You can clear it anytime by refreshing the page

## Uploading PDFs

### How to Upload

There are two ways to upload your PDF:

1. **Drag and Drop**
   - Simply drag your PDF file from your computer
   - Drop it onto the upload area
   - The upload will start automatically

2. **Click to Browse**
   - Click the "Browse Files" button
   - Select your PDF from the file dialog
   - Click "Open" to start the upload

### Upload Requirements

- **File Type**: Only PDF files are supported
- **File Size**: Maximum 10MB per file
- **Content**: Text-based PDFs work best (scanned images may not process correctly)

### Upload Progress

- You'll see a progress bar during upload
- The system processes and indexes your document
- Wait for the "Upload successful!" message
- You'll be automatically redirected to the chat interface

## Chatting with Your Documents

### Starting a Conversation

1. Type your question in the input field at the bottom
2. Press Enter or click "Send"
3. Wait for the response to stream in

### Types of Questions You Can Ask

- **Summarization**: "What is the main topic of this document?"
- **Specific Information**: "What does the document say about [topic]?"
- **Analysis**: "What are the key findings in this report?"
- **Comparison**: "How does section A relate to section B?"
- **Extraction**: "List all the recommendations mentioned"

### Conversation Features

- **Streaming Responses**: Answers appear in real-time as they're generated
- **Message History**: Your conversation is preserved during the session
- **Context Awareness**: The system remembers previous questions and answers

### Best Practices for Questions

1. **Be Specific**: Instead of "Tell me about this", ask "What are the three main conclusions?"
2. **Reference Sections**: "In the methodology section, how was the data collected?"
3. **Ask Follow-ups**: Build on previous answers for deeper understanding
4. **Request Formats**: "List the key points as bullet points"

## Understanding Sources

### What Are Sources?

Sources show you exactly which parts of your document were used to generate the answer. This provides:
- **Transparency**: See what information the answer is based on
- **Verification**: Check the original text yourself
- **Context**: Understand where in the document the information comes from

### Reading Source Information

Each source shows:
- **Page Number**: Which page the information is from
- **Text Excerpt**: The relevant paragraph or section
- **Relevance Score**: How closely the source matches your question (0-1 scale)

### Using Sources Effectively

- Click on sources to see more context
- Use page numbers to find information in your original PDF
- Higher relevance scores indicate stronger matches
- Multiple sources show comprehensive coverage of your question

## Tips and Best Practices

### For Best Results

1. **Quality PDFs**: Use text-based PDFs rather than scanned images
2. **Clear Questions**: Be specific about what you want to know
3. **Iterative Queries**: Start broad, then ask follow-up questions
4. **Document Structure**: Well-structured documents yield better results

### Advanced Usage

1. **Complex Analysis**
   ```
   "Compare the methodology in section 2 with the results in section 4. 
   Are there any inconsistencies?"
   ```

2. **Data Extraction**
   ```
   "Extract all numerical data from the results section and 
   format it as a table"
   ```

3. **Cross-Reference**
   ```
   "Find all mentions of 'sustainability' and summarize 
   the different contexts"
   ```

### Productivity Tips

- Keep related PDFs in a folder for easy access
- Take notes of important findings
- Export key conversations for future reference
- Use consistent naming for your PDFs

## Troubleshooting

### Common Issues and Solutions

#### "Upload Failed" Error
- **Check file size**: Must be under 10MB
- **Verify file type**: Only PDFs are supported
- **Try again**: Network issues may cause temporary failures

#### "API Key Invalid" Error
- **Check format**: Key should start with `sk-`
- **Verify key**: Ensure you copied it correctly
- **Check credits**: Ensure your OpenAI account has credits

#### No Sources Shown
- **Question too broad**: Try being more specific
- **Document quality**: Scanned PDFs may not index properly
- **Technical content**: Very technical documents may need specialized queries

#### Slow Responses
- **Document size**: Larger documents take longer to search
- **Question complexity**: Complex questions require more processing
- **Network speed**: Check your internet connection

### Getting Help

If you encounter issues:
1. Refresh the page and try again
2. Clear browser cache and cookies
3. Try a different browser
4. Check the console for error messages (F12 → Console)

## FAQ

### General Questions

**Q: How long are my documents stored?**
A: Documents are stored temporarily during your session. They're cleared when you close the browser.

**Q: Can I upload multiple PDFs?**
A: Currently, you work with one PDF at a time. Upload a new PDF to switch documents.

**Q: What languages are supported?**
A: The system works best with English documents, but can handle other languages that GPT-4 supports.

**Q: Is my data secure?**
A: Your documents are processed securely. API keys are stored locally, and documents aren't permanently stored.

### Technical Questions

**Q: What's the maximum document size?**
A: Individual PDFs can be up to 10MB. Documents are split into chunks for processing.

**Q: How accurate are the answers?**
A: Answers are based on the document content. The source citations let you verify accuracy.

**Q: Can I export my conversations?**
A: Currently, you can copy and paste conversations. Export features are planned for future releases.

**Q: Why can't I see images from my PDF?**
A: The system currently processes text only. Image analysis is not supported.

### Usage Questions

**Q: How many questions can I ask?**
A: There's no limit on questions per document during your session.

**Q: Can I go back to previous documents?**
A: You'll need to re-upload documents after starting a new session.

**Q: Do I need to pay for OpenAI API usage?**
A: Yes, you're using your own API key, so standard OpenAI pricing applies.

**Q: Can multiple people use the same API key?**
A: While technically possible, it's recommended each user has their own key for security and usage tracking.

## Advanced Features (Coming Soon)

- **Document Comparison**: Chat with multiple PDFs simultaneously
- **Export Functionality**: Save conversations and summaries
- **Annotation Tools**: Highlight and note important sections
- **Team Collaboration**: Share documents and conversations
- **API Integration**: Programmatic access for automation

---

*For technical documentation and API details, see the [API Documentation](API_DOCUMENTATION.md).*