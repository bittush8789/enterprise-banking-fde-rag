// ==============================================================================
// BankAssist AI — Authentication & Session Manager
// ==============================================================================

const Auth = {
  checkAuth() {
    const token = BankAPI.getAuthToken();
    if (!token) {
      if (!window.location.pathname.includes("login") && !window.location.pathname.endsWith("/")) {
        window.location.href = "/login";
      }
      return false;
    }
    return true;
  },

  getUser() {
    return BankAPI.getUserData();
  },

  hasRole(roleName) {
    const user = this.getUser();
    if (!user || !user.roles) return false;
    const roleNames = user.roles.map(r => (typeof r === "string" ? r : r.name).toUpperCase());
    return roleNames.includes("ADMIN") || roleNames.includes(roleName.toUpperCase());
  },

  isAdmin() {
    const user = this.getUser();
    if (!user || !user.roles) return false;
    const roleNames = user.roles.map(r => (typeof r === "string" ? r : r.name).toUpperCase());
    return roleNames.includes("ADMIN");
  },

  async initUser() {
    try {
      const user = await BankAPI.getCurrentUser();
      BankAPI.setUserData(user);
      return user;
    } catch (err) {
      console.error("Failed to fetch current user profile:", err);
      return null;
    }
  },

  logout() {
    BankAPI.removeAuthToken();
    window.location.href = "/login";
  }
};

window.Auth = Auth;
