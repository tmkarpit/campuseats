const endpoint = '/graphql';
const list = document.querySelector('#dish-list');
const message = document.querySelector('#message');
const form = document.querySelector('#add-form');
const nameInput = document.querySelector('#name');
const priceInput = document.querySelector('#price');
const availableInput = document.querySelector('#available');

async function graphql(query, variables = {}) {
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, variables })
  });
  const result = await response.json();
  if (!response.ok || result.errors) throw new Error(result.errors?.[0]?.message || 'Request failed');
  return result.data;
}

function show(text, kind = '') { message.className = kind; message.textContent = text; }
function render(dishes) {
  list.innerHTML = dishes.map(dish => `<article class="dish"><div><h2>${dish.name}</h2><p class="price">₹${dish.price.toFixed(2)}</p></div><span class="tag ${dish.available ? 'yes' : 'no'}">${dish.available ? 'Available' : 'Unavailable'}</span></article>`).join('');
}

async function loadDishes() {
  show('Loading menu…');
  try {
    const { dishes } = await graphql(`query { dishes { id name price available } }`);
    render(dishes); show(`${dishes.length} dishes loaded.`, 'success');
  } catch (error) { show(error.message, 'error'); }
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const input = { name: nameInput.value, price: Number(priceInput.value), available: availableInput.checked };
  try {
    const { addDish } = await graphql(`mutation AddDish($input: AddDishInput!) { addDish(input: $input) { id name price available } }`, { input });
    show(`${addDish.name} was added successfully.`, 'success');
    event.target.reset(); availableInput.checked = true;
    await loadDishes();
  } catch (error) { show(error.message, 'error'); }
});

loadDishes();
