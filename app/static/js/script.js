function showLogin() {
    document.getElementById('login-form').classList.remove('translate-x-full');
    document.getElementById('login-form').classList.add('translate-x-0');
  }
  
  function hideLogin() {
    document.getElementById('login-form').classList.remove('translate-x-0');
    document.getElementById('login-form').classList.add('translate-x-full');
  }