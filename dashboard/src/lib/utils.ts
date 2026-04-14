import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(dateStr: string): string {
  return new Date(dateStr + (dateStr.includes('T') ? '' : 'T00:00:00')).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
  }).format(value);
}

export function formatDateParam(date: Date): string {
  return date.toISOString().split('T')[0];
}

export function getDefaultStartDate(): string {
  const d = new Date();
  d.setDate(d.getDate() - 90);
  return formatDateParam(d);
}

export function getDefaultEndDate(): string {
  return formatDateParam(new Date());
}
