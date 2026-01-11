import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Allergy Prevention Agent',
  description: 'AI-powered allergy risk assessment and prevention',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
