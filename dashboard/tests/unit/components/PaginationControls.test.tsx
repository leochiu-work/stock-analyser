import { render, screen, fireEvent } from '@testing-library/react';
import { PaginationControls } from '@/components/shared/PaginationControls';

// The PaginationPrevious/PaginationNext components are built on @base-ui/react
// Button with render=<a>, which sets role="button" on the <a> element.
// So we query by role="button" and aria-label, not role="link".

describe('PaginationControls', () => {
  it('renders showing X–Y of Z text', () => {
    render(<PaginationControls total={100} offset={0} limit={50} onPageChange={() => {}} />);
    expect(screen.getByText(/Showing 1–50 of 100/)).toBeInTheDocument();
  });

  it('renders showing text for second page', () => {
    render(<PaginationControls total={100} offset={50} limit={50} onPageChange={() => {}} />);
    expect(screen.getByText(/Showing 51–100 of 100/)).toBeInTheDocument();
  });

  it('returns null when there is only one page', () => {
    const { container } = render(
      <PaginationControls total={30} offset={0} limit={50} onPageChange={() => {}} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders pagination nav when there is more than one page', () => {
    render(<PaginationControls total={100} offset={0} limit={50} onPageChange={() => {}} />);
    expect(screen.getByRole('navigation', { name: /pagination/i })).toBeInTheDocument();
  });

  it('calls onPageChange with next offset when Next is clicked', () => {
    const onPageChange = jest.fn();
    render(<PaginationControls total={100} offset={0} limit={50} onPageChange={onPageChange} />);
    fireEvent.click(screen.getByRole('button', { name: /go to next page/i }));
    expect(onPageChange).toHaveBeenCalledWith(50);
  });

  it('calls onPageChange with previous offset when Previous is clicked', () => {
    const onPageChange = jest.fn();
    render(<PaginationControls total={100} offset={50} limit={50} onPageChange={onPageChange} />);
    fireEvent.click(screen.getByRole('button', { name: /go to previous page/i }));
    expect(onPageChange).toHaveBeenCalledWith(0);
  });

  it('does not call onPageChange when Previous is clicked on first page', () => {
    const onPageChange = jest.fn();
    render(<PaginationControls total={100} offset={0} limit={50} onPageChange={onPageChange} />);
    fireEvent.click(screen.getByRole('button', { name: /go to previous page/i }));
    expect(onPageChange).not.toHaveBeenCalled();
  });

  it('Previous button has opacity-50 class on first page', () => {
    render(<PaginationControls total={100} offset={0} limit={50} onPageChange={() => {}} />);
    const prevBtn = screen.getByRole('button', { name: /go to previous page/i });
    expect(prevBtn).toHaveClass('opacity-50');
  });

  it('does not call onPageChange when Next is clicked on last page', () => {
    const onPageChange = jest.fn();
    render(<PaginationControls total={100} offset={50} limit={50} onPageChange={onPageChange} />);
    fireEvent.click(screen.getByRole('button', { name: /go to next page/i }));
    expect(onPageChange).not.toHaveBeenCalled();
  });

  it('Next button has opacity-50 class on last page', () => {
    render(<PaginationControls total={100} offset={50} limit={50} onPageChange={() => {}} />);
    const nextBtn = screen.getByRole('button', { name: /go to next page/i });
    expect(nextBtn).toHaveClass('opacity-50');
  });

  it('clamps previous offset to 0 when offset < limit', () => {
    const onPageChange = jest.fn();
    render(<PaginationControls total={100} offset={30} limit={50} onPageChange={onPageChange} />);
    fireEvent.click(screen.getByRole('button', { name: /go to previous page/i }));
    expect(onPageChange).toHaveBeenCalledWith(0);
  });
});
