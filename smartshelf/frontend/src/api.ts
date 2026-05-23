export const API_BASE_URL = "http://localhost:5000";
const BASE_URL = API_BASE_URL;

function getToken(): string | null {
  return localStorage.getItem("smartshelf_token");
}

export function setStoredToken(token: string | null) {
  if (token) localStorage.setItem("smartshelf_token", token);
  else localStorage.removeItem("smartshelf_token");
}

async function apiFetch<T>(
  path: string,
  options?: RequestInit
): Promise<{ success: boolean; data?: T; error?: string }> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  try {
    const res = await fetch(`${BASE_URL}${path}`, {
      headers,
      ...options,
    });
    try {
      return await res.json();
    } catch {
      return {
        success: false,
        error: `Server returned an invalid response (${res.status}).`,
      };
    }
  } catch {
    return {
      success: false,
      error: "Could not connect to server. Make sure the backend is running.",
    };
  }
}

export const api = {
  signup: (name: string, email: string, password: string) =>
    apiFetch<{ user: { id: number; name: string; email: string; is_admin: boolean }; token: string }>(
      "/signup",
      {
        method: "POST",
        body: JSON.stringify({ name, email, password }),
      }
    ),

  login: (email: string, password: string) =>
    apiFetch<{ user: { id: number; name: string; email: string; is_admin: boolean }; token: string }>(
      "/login",
      {
        method: "POST",
        body: JSON.stringify({ email, password }),
      }
    ),

  books: () => apiFetch<{ books: import("./types").Book[] }>("/books"),

  borrow: (book_id: number) =>
    apiFetch<{ message: string; due_date?: string }>("/borrow", {
      method: "POST",
      body: JSON.stringify({ book_id }),
    }),

  returnBook: (book_id: number) =>
    apiFetch<{ message: string }>("/return", {
      method: "POST",
      body: JSON.stringify({ book_id }),
    }),

  history: () => apiFetch<{ history: import("./types").Transaction[] }>("/history"),

  overdue: (user_id: number) =>
    apiFetch<{ overdue: import("./types").OverdueItem[] }>(`/overdue/${user_id}`),

  recommendations: () =>
    apiFetch<{ recommendations: import("./types").Recommendation[] }>("/recommendations"),

  adminAddBook: (book: {
    title: string;
    author: string;
    category: string;
    image_url: string;
    description: string;
  }) =>
    apiFetch<{ book: import("./types").Book }>("/admin/books", {
      method: "POST",
      body: JSON.stringify(book),
    }),

  adminDeleteBook: (book_id: number) =>
    apiFetch<{ message: string }>(`/admin/books/${book_id}`, { method: "DELETE" }),

  adminBorrows: () =>
    apiFetch<{ borrows: import("./types").AdminBorrow[] }>("/admin/borrows"),

  reserve: (book_id: number, user_id: number, amount: number) =>
    apiFetch<{ reservation: import("./types").ReservationConfirm }>("/reserve", {
      method: "POST",
      body: JSON.stringify({ book_id, user_id, amount }),
    }),

  recordDownloadPayment: (book_id: number, user_id: number, amount: number) =>
    apiFetch<{ message: string; borrow_id?: number }>("/api/download-payment", {
      method: "POST",
      body: JSON.stringify({ book_id, user_id, amount }),
    }),

  reservations: (user_id: number) =>
    apiFetch<{ reservations: import("./types").Reservation[] }>(`/reservations/${user_id}`),

  adminUploadPdf: async (book_id: number, file: File) => {
    const token = getToken();
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await fetch(`${BASE_URL}/admin/upload-pdf/${book_id}`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      });
      return await res.json();
    } catch {
      return {
        success: false,
        error: "Could not connect to server. Make sure the backend is running.",
      };
    }
  },
};
