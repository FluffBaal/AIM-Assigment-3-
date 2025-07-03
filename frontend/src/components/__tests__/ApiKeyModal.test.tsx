import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '../../test/test-utils';
import { ApiKeyModal } from '../ApiKeyModal';

describe('ApiKeyModal', () => {
  const mockOnSubmit = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the modal when open', () => {
    render(<ApiKeyModal isOpen={true} onSubmit={mockOnSubmit} />);
    
    expect(screen.getByText('Enter OpenAI API Key')).toBeInTheDocument();
    expect(screen.getByText('Please enter your OpenAI API key to use the chat functionality.')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('sk-...')).toBeInTheDocument();
    expect(screen.getByText('Submit')).toBeInTheDocument();
  });

  it('does not render when closed', () => {
    render(<ApiKeyModal isOpen={false} onSubmit={mockOnSubmit} />);
    
    expect(screen.queryByText('Enter OpenAI API Key')).not.toBeInTheDocument();
  });

  it('handles input changes', () => {
    render(<ApiKeyModal isOpen={true} onSubmit={mockOnSubmit} />);
    
    const input = screen.getByPlaceholderText('sk-...') as HTMLInputElement;
    fireEvent.change(input, { target: { value: 'sk-test-key' } });
    
    expect(input.value).toBe('sk-test-key');
  });

  it('shows error for invalid API key format', async () => {
    render(<ApiKeyModal isOpen={true} onSubmit={mockOnSubmit} />);
    
    const input = screen.getByPlaceholderText('sk-...');
    const submitButton = screen.getByText('Submit');
    
    fireEvent.change(input, { target: { value: 'invalid-key' } });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('API key must start with sk-')).toBeInTheDocument();
    });
    
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('shows error for empty API key', async () => {
    render(<ApiKeyModal isOpen={true} onSubmit={mockOnSubmit} />);
    
    const submitButton = screen.getByText('Submit');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('API key is required')).toBeInTheDocument();
    });
    
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('submits valid API key', async () => {
    render(<ApiKeyModal isOpen={true} onSubmit={mockOnSubmit} />);
    
    const input = screen.getByPlaceholderText('sk-...');
    const submitButton = screen.getByText('Submit');
    
    fireEvent.change(input, { target: { value: 'sk-valid-test-key' } });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith('sk-valid-test-key');
    });
  });

  it('handles form submission with Enter key', async () => {
    render(<ApiKeyModal isOpen={true} onSubmit={mockOnSubmit} />);
    
    const input = screen.getByPlaceholderText('sk-...');
    
    fireEvent.change(input, { target: { value: 'sk-valid-test-key' } });
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
    
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith('sk-valid-test-key');
    });
  });

  it('clears error when typing valid key', async () => {
    render(<ApiKeyModal isOpen={true} onSubmit={mockOnSubmit} />);
    
    const input = screen.getByPlaceholderText('sk-...');
    const submitButton = screen.getByText('Submit');
    
    // First submit invalid key
    fireEvent.change(input, { target: { value: 'invalid' } });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('API key must start with sk-')).toBeInTheDocument();
    });
    
    // Then type valid key
    fireEvent.change(input, { target: { value: 'sk-valid' } });
    
    await waitFor(() => {
      expect(screen.queryByText('API key must start with sk-')).not.toBeInTheDocument();
    });
  });

  it('shows loading state during submission', async () => {
    const slowSubmit = vi.fn().mockImplementation(() => 
      new Promise(resolve => setTimeout(resolve, 100))
    );
    
    render(<ApiKeyModal isOpen={true} onSubmit={slowSubmit} />);
    
    const input = screen.getByPlaceholderText('sk-...');
    const submitButton = screen.getByText('Submit');
    
    fireEvent.change(input, { target: { value: 'sk-valid-test-key' } });
    fireEvent.click(submitButton);
    
    expect(screen.getByText('Validating...')).toBeInTheDocument();
    expect(submitButton).toBeDisabled();
    
    await waitFor(() => {
      expect(screen.queryByText('Validating...')).not.toBeInTheDocument();
    });
  });
});