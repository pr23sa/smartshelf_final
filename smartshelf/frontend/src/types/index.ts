export interface User {
  id: number;
  name: string;
  email: string;
  is_admin?: boolean;
}

export interface Book {
  id: number;
  title: string;
  author: string;
  category: string;
  price: number;
  download_price: number;
  rent_price: number;
  image_url: string;
  description: string;
  pdf_path?: string | null;
  available: number;
}

export interface Reservation {
  id: number;
  user_id: number;
  book_id: number;
  reservation_id: string;
  status: string;
  reservation_date: string;
  due_date: string;
  amount_paid: number;
  title?: string;
  author?: string;
  image_url?: string;
  category?: string;
  user_name?: string;
  user_email?: string;
}

export interface MyReservation {
  id: number;
  user_id: number;
  book_id: number;
  reservation_id: string;
  status: string;
  reservation_date: string;
  due_date: string;
  pickup_deadline: string;
  display_status: "Active" | "Expired";
  amount_paid: number;
  title: string;
  author: string;
  image_url?: string;
  category?: string;
}

export interface ReservationConfirm {
  reservation_id: string;
  book_id: number;
  title: string;
  author: string;
  image_url: string;
  user_name: string;
  user_email: string;
  reservation_date: string;
  pickup_deadline?: string;
  due_date?: string | null;
  amount_paid: number;
  status: string;
}

export interface Transaction {
  id: number;
  book_id: number;
  title: string;
  author: string;
  image_url: string;
  price: number;
  category: string;
  status: "borrowed" | "returned";
  date: string;
  borrowed_at?: string;
  due_date?: string;
  days_overdue?: number;
}

export interface OverdueItem {
  id: number;
  book_id: number;
  title: string;
  author: string;
  image_url: string;
  price: number;
  category: string;
  borrowed_at?: string;
  due_date?: string;
  days_overdue: number;
}

export interface Recommendation {
  id: number;
  title: string;
  author: string;
  category: string;
  image_url: string;
  price: number;
  similarity_score: number;
}

export interface AdminBorrow {
  id: number;
  status: string;
  borrowed_at?: string;
  due_date?: string;
  user_id: number;
  user_name: string;
  user_email: string;
  book_id: number;
  title: string;
  author: string;
  category: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}
