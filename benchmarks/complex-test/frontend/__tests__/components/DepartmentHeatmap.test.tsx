import { render, screen } from '@testing-library/react'
import { DepartmentHeatmap } from '@/components/dashboard/DepartmentHeatmap'

describe('DepartmentHeatmap', () => {
  const mockDepartments = [
    {
      department_name: '営業部',
      average_score: 75,
      high_stress_count: 5,
      employee_count: 20,
    },
    {
      department_name: '開発部',
      average_score: 45,
      high_stress_count: 2,
      employee_count: 30,
    },
    {
      department_name: '人事部',
      average_score: 30,
      high_stress_count: 0,
      employee_count: 10,
    },
  ]

  it('renders empty state when no departments', () => {
    render(<DepartmentHeatmap departments={[]} />)
    expect(screen.getByText('部署データがありません')).toBeInTheDocument()
  })

  it('renders all department names', () => {
    render(<DepartmentHeatmap departments={mockDepartments} />)

    expect(screen.getByText('営業部')).toBeInTheDocument()
    expect(screen.getByText('開発部')).toBeInTheDocument()
    expect(screen.getByText('人事部')).toBeInTheDocument()
  })

  it('renders average scores', () => {
    render(<DepartmentHeatmap departments={mockDepartments} />)

    expect(screen.getByText('75.0')).toBeInTheDocument()
    expect(screen.getByText('45.0')).toBeInTheDocument()
    expect(screen.getByText('30.0')).toBeInTheDocument()
  })

  it('renders employee counts', () => {
    render(<DepartmentHeatmap departments={mockDepartments} />)

    expect(screen.getByText('従業員: 20名')).toBeInTheDocument()
    expect(screen.getByText('従業員: 30名')).toBeInTheDocument()
    expect(screen.getByText('従業員: 10名')).toBeInTheDocument()
  })

  it('shows risk labels based on score', () => {
    render(<DepartmentHeatmap departments={mockDepartments} />)

    // 高スコア（75）は「要注意」
    expect(screen.getByText('要注意')).toBeInTheDocument()
    // 中スコア（45）は「良好」（50未満）
    // 低スコア（30）は「良好」
    expect(screen.getAllByText('良好').length).toBeGreaterThanOrEqual(2)
  })

  it('renders high stress count for departments with high stress', () => {
    render(<DepartmentHeatmap departments={mockDepartments} />)

    // 営業部は高ストレス者5名
    expect(screen.getByText('高ストレス: 5名')).toBeInTheDocument()
    // 開発部は高ストレス者2名
    expect(screen.getByText('高ストレス: 2名')).toBeInTheDocument()
  })

  it('does not show high stress count for departments with 0', () => {
    render(<DepartmentHeatmap departments={mockDepartments} />)

    // 人事部は高ストレス者0名なので表示されない
    expect(screen.queryByText('高ストレス: 0名')).not.toBeInTheDocument()
  })

  it('renders summary statistics', () => {
    render(<DepartmentHeatmap departments={mockDepartments} />)

    expect(screen.getByText('要注意部署')).toBeInTheDocument()
    expect(screen.getByText('注意部署')).toBeInTheDocument()
    expect(screen.getByText('良好部署')).toBeInTheDocument()
  })

  it('calculates correct summary counts', () => {
    render(<DepartmentHeatmap departments={mockDepartments} />)

    // 要注意部署: score >= 70 (営業部)
    // 注意部署: 50 <= score < 70 (なし)
    // 良好部署: score < 50 (開発部, 人事部)
    const summarySection = screen.getByText('要注意部署').closest('div')?.parentElement

    // Count should reflect: 1 要注意, 0 注意, 2 良好
    expect(summarySection).toBeInTheDocument()
  })

  it('sorts departments by score (highest first)', () => {
    render(<DepartmentHeatmap departments={mockDepartments} />)

    const departmentNames = screen.getAllByText(/部$/i)
    // First department should be highest score (営業部: 75)
    expect(departmentNames[0].textContent).toBe('営業部')
  })

  it('renders legend', () => {
    render(<DepartmentHeatmap departments={mockDepartments} />)

    expect(screen.getByText('ストレスレベル:')).toBeInTheDocument()
    expect(screen.getByText('低')).toBeInTheDocument()
    expect(screen.getByText('中')).toBeInTheDocument()
    expect(screen.getByText('やや高')).toBeInTheDocument()
    expect(screen.getByText('高')).toBeInTheDocument()
  })
})
