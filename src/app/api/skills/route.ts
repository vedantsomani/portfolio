import { NextRequest, NextResponse } from 'next/server'

// Get skills data
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const category = searchParams.get('category')

    // Import skills data
    const { skills } = await import('@/data/portfolio')

    let filteredSkills = skills

    // Filter by category
    if (category) {
      filteredSkills = skills.filter(
        skill => skill.category.toLowerCase().includes(category.toLowerCase())
      )
    }

    return NextResponse.json({
      skills: filteredSkills,
      categories: skills.map(s => s.category)
    })

  } catch (error) {
    console.error('Skills API error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch skills' },
      { status: 500 }
    )
  }
}
