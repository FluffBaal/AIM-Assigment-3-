import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '../../test/test-utils';
import { PDFUpload } from '../PDFUpload';
import { apiClient } from '../../services/api';

// Mock the API client
vi.mock('../../services/api', () => ({
  apiClient: {
    uploadPDF: vi.fn(),
  },
}));

// Mock the useApiKey hook
vi.mock('../../hooks/useApiKey', () => ({
  useApiKey: () => ({ apiKey: 'sk-test-key' }),
}));

describe('PDFUpload', () => {
  const mockOnFileUploaded = vi.fn();
  const mockFile = new File(['test pdf content'], 'test.pdf', {
    type: 'application/pdf',
  });

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders upload area', () => {
    render(<PDFUpload onFileUploaded={mockOnFileUploaded} />);
    
    expect(screen.getByText('Upload PDF')).toBeInTheDocument();
    expect(screen.getByText(/Drag and drop your PDF here/)).toBeInTheDocument();
    expect(screen.getByText('Browse Files')).toBeInTheDocument();
  });

  it('handles file selection via button click', async () => {
    const mockUploadResponse = { file_id: 'test-123', filename: 'test.pdf' };
    (apiClient.uploadPDF as any).mockResolvedValue(mockUploadResponse);

    render(<PDFUpload onFileUploaded={mockOnFileUploaded} />);
    
    const input = screen.getByTestId('file-input') as HTMLInputElement;
    
    fireEvent.change(input, { target: { files: [mockFile] } });
    
    await waitFor(() => {
      expect(apiClient.uploadPDF).toHaveBeenCalledWith(mockFile, 'sk-test-key');
      expect(mockOnFileUploaded).toHaveBeenCalledWith('test-123');
    });
  });

  it('shows error for non-PDF files', async () => {
    render(<PDFUpload onFileUploaded={mockOnFileUploaded} />);
    
    const nonPdfFile = new File(['content'], 'test.txt', { type: 'text/plain' });
    const input = screen.getByTestId('file-input');
    
    fireEvent.change(input, { target: { files: [nonPdfFile] } });
    
    await waitFor(() => {
      expect(screen.getByText('Please select a PDF file')).toBeInTheDocument();
      expect(apiClient.uploadPDF).not.toHaveBeenCalled();
    });
  });

  it('handles drag and drop', async () => {
    const mockUploadResponse = { file_id: 'test-123', filename: 'test.pdf' };
    (apiClient.uploadPDF as any).mockResolvedValue(mockUploadResponse);

    render(<PDFUpload onFileUploaded={mockOnFileUploaded} />);
    
    const dropZone = screen.getByTestId('drop-zone');
    
    // Simulate drag enter
    fireEvent.dragEnter(dropZone);
    expect(dropZone).toHaveClass('border-indigo-600');
    
    // Simulate drop
    fireEvent.drop(dropZone, {
      dataTransfer: {
        files: [mockFile],
      },
    });
    
    await waitFor(() => {
      expect(apiClient.uploadPDF).toHaveBeenCalledWith(mockFile, 'sk-test-key');
      expect(mockOnFileUploaded).toHaveBeenCalledWith('test-123');
    });
  });

  it('prevents default drag behavior', () => {
    render(<PDFUpload onFileUploaded={mockOnFileUploaded} />);
    
    const dropZone = screen.getByTestId('drop-zone');
    
    const dragOverEvent = new Event('dragover', { bubbles: true });
    const preventDefaultSpy = vi.spyOn(dragOverEvent, 'preventDefault');
    
    fireEvent(dropZone, dragOverEvent);
    
    expect(preventDefaultSpy).toHaveBeenCalled();
  });

  it('shows uploading state', async () => {
    const mockUploadResponse = { file_id: 'test-123', filename: 'test.pdf' };
    let resolveUpload: any;
    const uploadPromise = new Promise((resolve) => {
      resolveUpload = resolve;
    });
    (apiClient.uploadPDF as any).mockReturnValue(uploadPromise);

    render(<PDFUpload onFileUploaded={mockOnFileUploaded} />);
    
    const input = screen.getByTestId('file-input');
    fireEvent.change(input, { target: { files: [mockFile] } });
    
    // Check loading state
    expect(screen.getByText('Uploading...')).toBeInTheDocument();
    expect(screen.getByText('Processing test.pdf')).toBeInTheDocument();
    
    // Resolve the upload
    resolveUpload(mockUploadResponse);
    
    await waitFor(() => {
      expect(screen.queryByText('Uploading...')).not.toBeInTheDocument();
    });
  });

  it('handles upload errors', async () => {
    const errorMessage = 'Upload failed';
    (apiClient.uploadPDF as any).mockRejectedValue(new Error(errorMessage));

    render(<PDFUpload onFileUploaded={mockOnFileUploaded} />);
    
    const input = screen.getByTestId('file-input');
    fireEvent.change(input, { target: { files: [mockFile] } });
    
    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
      expect(mockOnFileUploaded).not.toHaveBeenCalled();
    });
  });

  it('resets drag state on drag leave', () => {
    render(<PDFUpload onFileUploaded={mockOnFileUploaded} />);
    
    const dropZone = screen.getByTestId('drop-zone');
    
    fireEvent.dragEnter(dropZone);
    expect(dropZone).toHaveClass('border-indigo-600');
    
    fireEvent.dragLeave(dropZone);
    expect(dropZone).not.toHaveClass('border-indigo-600');
  });

  it('shows success state after upload', async () => {
    const mockUploadResponse = { file_id: 'test-123', filename: 'test.pdf' };
    (apiClient.uploadPDF as any).mockResolvedValue(mockUploadResponse);

    render(<PDFUpload onFileUploaded={mockOnFileUploaded} />);
    
    const input = screen.getByTestId('file-input');
    fireEvent.change(input, { target: { files: [mockFile] } });
    
    await waitFor(() => {
      expect(screen.getByText('Upload successful!')).toBeInTheDocument();
      expect(screen.getByText('test.pdf uploaded successfully')).toBeInTheDocument();
    });
  });

  it('allows re-upload after success', async () => {
    const mockUploadResponse = { file_id: 'test-123', filename: 'test.pdf' };
    (apiClient.uploadPDF as any).mockResolvedValue(mockUploadResponse);

    render(<PDFUpload onFileUploaded={mockOnFileUploaded} />);
    
    // First upload
    const input = screen.getByTestId('file-input') as HTMLInputElement;
    fireEvent.change(input, { target: { files: [mockFile] } });
    
    await waitFor(() => {
      expect(screen.getByText('Upload successful!')).toBeInTheDocument();
    });
    
    // Click to upload again
    fireEvent.click(screen.getByText('Upload Another PDF'));
    
    // Should show upload UI again
    expect(screen.getByText('Upload PDF')).toBeInTheDocument();
    expect(screen.queryByText('Upload successful!')).not.toBeInTheDocument();
  });
});