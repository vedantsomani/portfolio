import { NextRequest, NextResponse } from 'next/server'

// Get projects with optional filtering
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const category = searchParams.get('category')
    const featured = searchParams.get('featured')
    const limit = searchParams.get('limit')

    // Import projects data
    const { projects } = await import('@/data/portfolio')

    let filteredProjects = projects

    // Filter by category
    if (category && category !== 'All') {
      filteredProjects = filteredProjects.filter(
        project => project.category === category
      )
    }

    // Filter by featured status
    if (featured === 'true') {
      filteredProjects = filteredProjects.filter(
        project => project.featured === true
      )
    }

    // Limit results
    if (limit) {
      const limitNum = parseInt(limit)
      if (!isNaN(limitNum) && limitNum > 0) {
        filteredProjects = filteredProjects.slice(0, limitNum)
      }
    }

    return NextResponse.json({
      projects: filteredProjects,
      total: filteredProjects.length,
      categories: [...new Set(projects.map(p => p.category))]
    })

  } catch (error) {
    console.error('Projects API error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch projects' },
      { status: 500 }
    )
  }
}
