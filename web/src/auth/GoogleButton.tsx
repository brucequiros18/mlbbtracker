import { useEffect, useRef, useState } from 'react'

/**
 * The Google Sign-In button (Google Identity Services).
 *
 * The button itself is rendered by Google; we only supply the client ID and
 * receive the ID token back. The token is verified **on the server** - the
 * browser never decides who the player is.
 *
 * When no client ID is configured the button is replaced by an honest
 * "not configured" notice instead of a control that cannot work.
 */

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string
            callback: (response: { credential: string }) => void
            ux_mode?: string
            cancel_on_tap_outside?: boolean
          }) => void
          renderButton: (parent: HTMLElement, options: Record<string, unknown>) => void
          prompt: () => void
          cancel: () => void
        }
      }
    }
  }
}

const GIS_SRC = 'https://accounts.google.com/gsi/client'

let gisPromise: Promise<void> | null = null

function loadGis(): Promise<void> {
  if (window.google?.accounts?.id) return Promise.resolve()
  if (gisPromise) return gisPromise

  gisPromise = new Promise<void>((resolve, reject) => {
    const existing = document.querySelector<HTMLScriptElement>(`script[src="${GIS_SRC}"]`)
    if (existing) {
      existing.addEventListener('load', () => resolve())
      existing.addEventListener('error', () => reject(new Error('Google sign-in could not load.')))
      return
    }

    const script = document.createElement('script')
    script.src = GIS_SRC
    script.async = true
    script.defer = true
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('Google sign-in could not load.'))
    document.head.appendChild(script)
  })

  return gisPromise
}

interface GoogleButtonProps {
  clientId: string
  onCredential: (credential: string) => void
  onError?: (message: string) => void
  disabled?: boolean
}

export function GoogleButton({ clientId, onCredential, onError, disabled }: GoogleButtonProps) {
  const container = useRef<HTMLDivElement>(null)
  const [ready, setReady] = useState(false)
  const [failed, setFailed] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    loadGis()
      .then(() => {
        if (cancelled || !container.current || !window.google?.accounts?.id) return

        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: (response) => {
            if (response?.credential) onCredential(response.credential)
          },
        })

        window.google.accounts.id.renderButton(container.current, {
          type: 'standard',
          theme: 'filled_black',
          size: 'large',
          shape: 'pill',
          width: 320,
          text: 'continue_with',
          logo_alignment: 'left',
        })

        setReady(true)
      })
      .catch((error: Error) => {
        if (cancelled) return
        setFailed(error.message)
        onError?.(error.message)
      })

    return () => {
      cancelled = true
    }
  }, [clientId, onCredential, onError])

  if (failed) {
    return (
      <p className="rounded-control border border-negative/40 bg-negative/10 px-4 py-3 text-sm text-negative">
        {failed} Sign-in needs a connection to Google.
      </p>
    )
  }

  return (
    <div className="flex min-h-[44px] items-center justify-center">
      <div ref={container} className={ready ? '' : 'opacity-0'} aria-hidden={!ready} />
      {!ready && !failed ? (
        <span className="text-sm text-muted">Loading Google sign-in…</span>
      ) : null}
      {disabled ? <span className="sr-only">Sign-in unavailable</span> : null}
    </div>
  )
}
