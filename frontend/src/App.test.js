import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import App from './App'

const author = {
  id: 1,
  email: 'anna@example.com',
  username: 'anna',
  first_name: 'Анна',
  last_name: 'Петрова',
  is_subscribed: false
}

const tag = { id: 1, name: 'Завтрак', color: '#E26C2D', slug: 'breakfast' }

const recipe = {
  id: 1,
  author,
  tags: [tag],
  name: 'Сырники',
  image: 'http://localhost/media/recipes/syrniki.png',
  text: 'Творог, яйцо и немного муки.',
  cooking_time: 20,
  ingredients: [{ id: 1, name: 'творог', measurement_unit: 'г', amount: 200 }],
  is_favorited: false,
  is_in_shopping_cart: false
}

const response = (data, status = 200) => ({ status, json: () => Promise.resolve(data) })

// Answers the API requests by "METHOD /path/"; any other request gets 404.
const mockApi = routes => {
  global.fetch = jest.fn((url, options = {}) => {
    const handler = routes[`${options.method || 'GET'} ${url.split('?')[0]}`]
    return handler ? handler() : Promise.resolve(response({ detail: 'Not found.' }, 404))
  })
}

const renderAt = path => render(
  <MemoryRouter initialEntries={[path]}>
    <App />
  </MemoryRouter>
)

afterEach(() => localStorage.clear())

test('shows the recipes from the API', async () => {
  mockApi({
    'GET /api/tags/': () => Promise.resolve(response([tag])),
    'GET /api/recipes/': () => Promise.resolve(response({ count: 1, next: null, previous: null, results: [recipe] }))
  })

  renderAt('/recipes')

  expect(await screen.findByText('Сырники')).toBeInTheDocument()
})

test('offers the subscription only after the recipe has loaded', async () => {
  localStorage.setItem('token', 'reader-token')
  let sendRecipe
  mockApi({
    'GET /api/users/me/': () => Promise.resolve(response({ ...author, id: 2, username: 'reader' })),
    'GET /api/recipes/': () => Promise.resolve(response({ count: 0, next: null, previous: null, results: [] })),
    'GET /api/recipes/1/': () => new Promise(resolve => {
      sendRecipe = () => resolve(response(recipe))
    }),
    'POST /api/users/1/subscribe/': () => Promise.resolve(response({ ...author, is_subscribed: true }, 201))
  })

  renderAt('/recipes/1')

  // The recipe is requested but has not arrived yet: its author is unknown.
  await waitFor(() => expect(sendRecipe).toBeDefined())
  expect(screen.queryByText('Подписаться на автора')).not.toBeInTheDocument()

  sendRecipe()
  userEvent.click(await screen.findByText('Подписаться на автора'))

  expect(await screen.findByText('Отписаться от автора')).toBeInTheDocument()
  expect(global.fetch).toHaveBeenCalledWith(
    '/api/users/1/subscribe/',
    expect.objectContaining({ method: 'POST' })
  )
})
