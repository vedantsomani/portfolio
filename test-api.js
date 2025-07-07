// Simple test file to verify API endpoints
// Run with: node test-api.js

const testEndpoints = async () => {
  const baseUrl = 'http://localhost:3000'
  
  console.log('🧪 Testing API Endpoints...\n')
  
  // Test 1: Projects API
  try {
    const projectsResponse = await fetch(`${baseUrl}/api/projects`)
    const projectsData = await projectsResponse.json()
    console.log('✅ Projects API:', projectsData.total, 'projects found')
  } catch (error) {
    console.error('❌ Projects API failed:', error.message)
  }
  
  // Test 2: Skills API
  try {
    const skillsResponse = await fetch(`${baseUrl}/api/skills`)
    const skillsData = await skillsResponse.json()
    console.log('✅ Skills API:', skillsData.skills.length, 'skill categories found')
  } catch (error) {
    console.error('❌ Skills API failed:', error.message)
  }
  
  // Test 3: Contact API (POST)
  try {
    const contactResponse = await fetch(`${baseUrl}/api/contact`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: 'Test User',
        email: 'test@example.com',
        subject: 'Test Subject',
        message: 'This is a test message from the API test script.'
      })
    })
    const contactData = await contactResponse.json()
    console.log('✅ Contact API:', contactData.message || contactData.error)
  } catch (error) {
    console.error('❌ Contact API failed:', error.message)
  }
  
  // Test 4: Analytics API
  try {
    const analyticsResponse = await fetch(`${baseUrl}/api/analytics`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        event: 'test_event',
        page: 'test',
        data: { test: true }
      })
    })
    const analyticsData = await analyticsResponse.json()
    console.log('✅ Analytics API:', analyticsData.success ? 'Working' : 'Failed')
  } catch (error) {
    console.error('❌ Analytics API failed:', error.message)
  }
  
  console.log('\n🎉 API testing completed!')
}

// Run tests if this file is executed directly
if (typeof window === 'undefined') {
  testEndpoints()
}

export default testEndpoints
