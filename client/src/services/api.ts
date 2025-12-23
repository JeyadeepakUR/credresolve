import type {
  User,
  Group,
  Expense,
  Balance,
  Settlement,
  UserBalance,
  CreateUserData,
  CreateGroupData,
  CreateExpenseData,
  CreateSettlementData,
  RegisterData,
  LoginData,
  AuthResponse,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000/api';

class ApiService {
  private token: string | null = null;

  constructor() {
    // Use sessionStorage for per-tab isolation (not shared across browser tabs)
    this.token = sessionStorage.getItem('token');
  }

  setToken(token: string) {
    this.token = token;
    sessionStorage.setItem('token', token);
  }

  clearToken() {
    this.token = null;
    sessionStorage.removeItem('token');
  }

  private headers(contentTypeJson = true) {
    const headers: Record<string, string> = {};
    if (contentTypeJson) headers['Content-Type'] = 'application/json';
    if (this.token) headers['Authorization'] = `Bearer ${this.token}`;
    return headers;
  }

  // Auth
  async register(data: RegisterData): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: this.headers(),
      body: JSON.stringify(data),
    });
    const json = await response.json();
    if (!response.ok) {
      throw new Error(json.error?.message || 'Failed to register');
    }
    return json;
  }

  async login(data: LoginData): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: this.headers(),
      body: JSON.stringify(data),
    });
    const json = await response.json();
    if (!response.ok) {
      throw new Error(json.error?.message || 'Failed to login');
    }
    return json;
  }

  async me(): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: this.headers(false),
    });
    if (!response.ok) throw new Error('Failed to fetch current user');
    const data = await response.json();
    return data.user || data; // Backend returns { user: {...} }
  }

  // Users
  async getUsers(): Promise<User[]> {
    const response = await fetch(`${API_BASE_URL}/users`, { headers: this.headers(false) });
    if (!response.ok) throw new Error('Failed to fetch users');
    return response.json();
  }

  async getUser(userId: string): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/users/${userId}`, { headers: this.headers(false) });
    if (!response.ok) throw new Error('Failed to fetch user');
    return response.json();
  }

  async createUser(data: CreateUserData): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/users`, {
      method: 'POST',
      headers: this.headers(),
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error?.message || 'Failed to create user');
    }
    return response.json();
  }

  async getUserBalances(userId: string): Promise<UserBalance> {
    const response = await fetch(`${API_BASE_URL}/users/${userId}/balances`, {
      headers: this.headers(false),
    });
    if (!response.ok) throw new Error('Failed to fetch user balances');
    return response.json();
  }

  // Groups
  async getGroups(): Promise<Group[]> {
    const response = await fetch(`${API_BASE_URL}/groups`, { headers: this.headers(false) });
    if (!response.ok) throw new Error('Failed to fetch groups');
    return response.json();
  }

  async getGroup(groupId: string): Promise<Group> {
    const response = await fetch(`${API_BASE_URL}/groups/${groupId}`, { headers: this.headers(false) });
    if (!response.ok) throw new Error('Failed to fetch group');
    return response.json();
  }

  async createGroup(data: CreateGroupData): Promise<Group> {
    const response = await fetch(`${API_BASE_URL}/groups`, {
      method: 'POST',
      headers: this.headers(),
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error?.message || 'Failed to create group');
    }
    return response.json();
  }

  async addMemberToGroup(groupId: string, userId: string): Promise<Group> {
    const response = await fetch(`${API_BASE_URL}/groups/${groupId}/members`, {
      method: 'POST',
      headers: this.headers(),
      body: JSON.stringify({ userId }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error?.message || 'Failed to add member');
    }
    return response.json();
  }

  async getGroupExpenses(groupId: string): Promise<Expense[]> {
    const response = await fetch(`${API_BASE_URL}/groups/${groupId}/expenses`, { headers: this.headers(false) });
    if (!response.ok) throw new Error('Failed to fetch group expenses');
    return response.json();
  }

  async getGroupBalances(groupId: string): Promise<Balance[]> {
    const response = await fetch(`${API_BASE_URL}/groups/${groupId}/balances`, { headers: this.headers(false) });
    if (!response.ok) throw new Error('Failed to fetch group balances');
    return response.json();
  }

  async getSimplifiedBalances(groupId: string): Promise<Balance[]> {
    const response = await fetch(`${API_BASE_URL}/groups/${groupId}/balances/simplified`, { headers: this.headers(false) });
    if (!response.ok) throw new Error('Failed to fetch simplified balances');
    const data = await response.json();
    return data.simplifiedTransactions;
  }

  // Expenses
  async addExpense(data: any): Promise<{ expense: Expense; updatedBalances: Balance[] }> {
    const response = await fetch(`${API_BASE_URL}/expenses`, {
      method: 'POST',
      headers: this.headers(),
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error?.message || 'Failed to create expense');
    }
    return response.json();
  }

  async getExpense(expenseId: string): Promise<Expense> {
    const response = await fetch(`${API_BASE_URL}/expenses/${expenseId}`, { headers: this.headers(false) });
    if (!response.ok) throw new Error('Failed to fetch expense');
    return response.json();
  }

  async deleteExpense(expenseId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/expenses/${expenseId}`, {
      method: 'DELETE',
      headers: this.headers(false),
    });
    if (!response.ok) throw new Error('Failed to delete expense');
  }

  // Settlements
  async createSettlement(data: CreateSettlementData): Promise<{ settlement: Settlement; remainingBalance: number }> {
    const response = await fetch(`${API_BASE_URL}/settlements`, {
      method: 'POST',
      headers: this.headers(),
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error?.message || 'Failed to create settlement');
    }
    return response.json();
  }

  // Backward-compatible alias used by UI
  async recordSettlement(data: CreateSettlementData): Promise<{ settlement: Settlement; remainingBalance: number }> {
    return this.createSettlement(data);
  }

  async getGroupSettlements(groupId: string): Promise<Settlement[]> {
    const response = await fetch(`${API_BASE_URL}/settlements/groups/${groupId}`, { headers: this.headers(false) });
    if (!response.ok) throw new Error('Failed to fetch settlements');
    return response.json();
  }
}

export const apiService = new ApiService();
