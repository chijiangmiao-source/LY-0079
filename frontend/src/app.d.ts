/// <reference types="@sveltejs/kit" />

declare global {
  namespace App {
    interface Locals {
      user?: {
        id: number;
        username: string;
        role: string;
        full_name: string;
      };
    }
    interface PageData {
      user?: {
        id: number;
        username: string;
        role: string;
        full_name: string;
      };
    }
  }
}

export {};
