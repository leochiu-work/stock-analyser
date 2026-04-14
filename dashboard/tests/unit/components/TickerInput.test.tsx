import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TickerInput } from '@/components/shared/TickerInput';

describe('TickerInput', () => {
  it('renders input with correct placeholder', () => {
    render(<TickerInput value="" onChange={() => {}} />);
    expect(screen.getByPlaceholderText('Ticker (e.g. AAPL)')).toBeInTheDocument();
  });

  it('has correct aria-label', () => {
    render(<TickerInput value="" onChange={() => {}} />);
    expect(screen.getByRole('textbox', { name: 'Stock ticker symbol' })).toBeInTheDocument();
  });

  it('calls onChange with uppercased value when user types', async () => {
    const onChange = jest.fn();
    render(<TickerInput value="" onChange={onChange} />);
    const input = screen.getByRole('textbox');
    await userEvent.type(input, 'a');
    expect(onChange).toHaveBeenCalledWith('A');
  });

  it('calls onChange with uppercased value for lowercase input', async () => {
    const onChange = jest.fn();
    render(<TickerInput value="" onChange={onChange} />);
    const input = screen.getByRole('textbox');
    await userEvent.type(input, 'g');
    expect(onChange).toHaveBeenCalledWith('G');
  });

  it('shows badge when value is non-empty', () => {
    render(<TickerInput value="AAPL" onChange={() => {}} />);
    expect(screen.getByText('AAPL')).toBeInTheDocument();
  });

  it('does not show badge when value is empty', () => {
    render(<TickerInput value="" onChange={() => {}} />);
    // Badge renders the ticker text; when empty no badge is rendered
    expect(screen.queryByText(/[A-Z]+/)).not.toBeInTheDocument();
  });

  it('calls onSubmit when Enter is pressed', () => {
    const onSubmit = jest.fn();
    render(<TickerInput value="AAPL" onChange={() => {}} onSubmit={onSubmit} />);
    const input = screen.getByRole('textbox');
    fireEvent.keyDown(input, { key: 'Enter' });
    expect(onSubmit).toHaveBeenCalledTimes(1);
  });

  it('does not error when onSubmit is not provided and Enter is pressed', () => {
    render(<TickerInput value="AAPL" onChange={() => {}} />);
    const input = screen.getByRole('textbox');
    expect(() => fireEvent.keyDown(input, { key: 'Enter' })).not.toThrow();
  });

  it('does not call onSubmit for other keys', () => {
    const onSubmit = jest.fn();
    render(<TickerInput value="AAPL" onChange={() => {}} onSubmit={onSubmit} />);
    const input = screen.getByRole('textbox');
    fireEvent.keyDown(input, { key: 'a' });
    expect(onSubmit).not.toHaveBeenCalled();
  });
});
