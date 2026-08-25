export default async function stagingSetup() {
  const stagingApiUrl = process.env.STAGING_API_URL
  if (!stagingApiUrl) return

  let healthUrl: URL
  try {
    healthUrl = new URL('/health', stagingApiUrl)
  } catch {
    throw new Error('STAGING_API_URL must be an absolute URL.')
  }

  const response = await fetch(healthUrl)
  if (!response.ok) throw new Error(`Staging API health check failed with HTTP ${response.status}.`)
}
