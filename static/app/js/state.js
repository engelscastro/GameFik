// ==================== STATE MANAGEMENT ====================
const state = {
    user: null,
    missions: [],
    achievements: [],
    rewards: [],
    disciplines: [],
    users: [],
    currentPage: 'dashboard'
};

// Observers para mudanças de estado
const stateObservers = [];

function subscribeToState(observer) {
    stateObservers.push(observer);
}

function notifyStateChange(key, value) {
    stateObservers.forEach(observer => observer(key, value));
}

function updateState(key, value) {
    state[key] = value;
    notifyStateChange(key, value);
}