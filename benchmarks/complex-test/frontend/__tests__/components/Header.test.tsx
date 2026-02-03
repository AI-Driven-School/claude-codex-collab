import { render, screen, fireEvent } from '@testing-library/react'
import { Header } from '@/components/ui/header'

// Mock authApi
jest.mock('@/lib/api/auth', () => ({
  authApi: {
    logout: jest.fn().mockResolvedValue(undefined),
  },
}))

// Mock useRouter
const mockPush = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: jest.fn(),
    prefetch: jest.fn(),
    back: jest.fn(),
  }),
}))

describe('Header', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders the app name', () => {
    render(<Header />)
    expect(screen.getByText('StressAgent Pro')).toBeInTheDocument()
  })

  it('renders the title when provided', () => {
    render(<Header title="Dashboard" />)
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
  })

  it('renders logout button by default', () => {
    render(<Header />)
    expect(screen.getByText('ログアウト')).toBeInTheDocument()
  })

  it('hides logout button when showLogout is false', () => {
    render(<Header showLogout={false} />)
    expect(screen.queryByText('ログアウト')).not.toBeInTheDocument()
  })

  it('shows home button when showHome is true', () => {
    render(<Header showHome={true} />)
    expect(screen.getByLabelText('ホーム')).toBeInTheDocument()
  })

  it('hides home button by default', () => {
    render(<Header />)
    expect(screen.queryByLabelText('ホーム')).not.toBeInTheDocument()
  })

  it('navigates to login on logout', async () => {
    const { authApi } = require('@/lib/api/auth')
    render(<Header />)

    const logoutButton = screen.getByText('ログアウト')
    fireEvent.click(logoutButton)

    // Wait for the async logout to complete
    await new Promise(resolve => setTimeout(resolve, 0))

    expect(authApi.logout).toHaveBeenCalled()
    expect(mockPush).toHaveBeenCalledWith('/login')
  })

  it('navigates to home when home button is clicked', () => {
    render(<Header showHome={true} />)

    const homeButton = screen.getByLabelText('ホーム')
    fireEvent.click(homeButton)

    expect(mockPush).toHaveBeenCalledWith('/home')
  })

  it('renders custom actions', () => {
    render(
      <Header
        actions={<button data-testid="custom-action">Custom</button>}
      />
    )
    expect(screen.getByTestId('custom-action')).toBeInTheDocument()
  })
})
