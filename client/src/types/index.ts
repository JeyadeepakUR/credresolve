// API Types
export interface User {
  id: string;
  name: string;
  email: string;
  createdAt: string;
}

export interface Group {
  id: string;
  name: string;
  description: string;
  members: string[];
  createdBy: string;
  createdAt: string;
}

export interface Expense {
  id: string;
  groupId: string;
  description: string;
  totalAmount: number;
  paidBy: string;
  splitType: 'EQUAL' | 'EXACT' | 'PERCENTAGE';
  splits: Split[];
  createdAt: string;
}

export interface Split {
  userId: string;
  amount?: number;
  percentage?: number;
}

export interface Balance {
  groupId: string;
  fromUserId: string;
  toUserId: string;
  amount: number;
}

export interface Settlement {
  id: string;
  groupId: string;
  fromUserId: string;
  toUserId: string;
  amount: number;
  settledAt: string;
}

export interface UserBalance {
  userId: string;
  owes: Balance[];
  owed: Balance[];
  netBalance: number;
}

export interface CreateUserData {
  name: string;
  email: string;
}

export interface RegisterData {
  name: string;
  email: string;
  password: string;
}

export interface LoginData {
  email: string;
  password: string;
}

export interface AuthResponse {
  token: string;
  user: User;
}

export interface CreateGroupData {
  name: string;
  description: string;
  createdBy: string;
}

export interface CreateExpenseData {
  groupId: string;
  description: string;
  totalAmount: number;
  paidBy: string;
  splitType: 'EQUAL' | 'EXACT' | 'PERCENTAGE';
  splits: Split[];
}

export interface CreateSettlementData {
  groupId: string;
  fromUserId: string;
  toUserId: string;
  amount: number;
}

export interface SimplifiedBalances {
  groupId: string;
  simplifiedTransactions: Balance[];
  transactionCount: number;
}
