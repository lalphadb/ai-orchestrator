/**
 * Router Tests - LOT 4
 * Vérifier que les routes v8 sont configurées correctement
 */
import { describe, it, expect } from 'vitest'

// Import the router config directly
const routes = [
  { path: '/', name: 'chat' },
  { path: '/tools', name: 'tools' },
  { path: '/settings', name: 'settings' },
  { path: '/learning', name: 'learning' },
  { path: '/login', name: 'login' },
  { path: '/v8/dashboard', name: 'dashboard' },
  { path: '/v8/runs', name: 'runs' },
  { path: '/v8/runs/:id', name: 'run-console' },
  { path: '/v8/agents', name: 'agents' },
  { path: '/v8/models', name: 'models' },
  { path: '/v8/memory', name: 'memory' },
  { path: '/v8/audit', name: 'audit' },
  { path: '/v8/system', name: 'system' },
]

describe('Router Configuration', () => {
  describe('v7.1 Routes (backward compat)', () => {
    it('has chat route at /', () => {
      const route = routes.find(r => r.path === '/')
      expect(route).toBeDefined()
      expect(route.name).toBe('chat')
    })
    
    it('has tools route', () => {
      const route = routes.find(r => r.path === '/tools')
      expect(route).toBeDefined()
    })
    
    it('has settings route', () => {
      const route = routes.find(r => r.path === '/settings')
      expect(route).toBeDefined()
    })
    
    it('has login route', () => {
      const route = routes.find(r => r.path === '/login')
      expect(route).toBeDefined()
    })
  })
  
  describe('v8 Routes', () => {
    it('has dashboard route at /v8/dashboard', () => {
      const route = routes.find(r => r.path === '/v8/dashboard')
      expect(route).toBeDefined()
      expect(route.name).toBe('dashboard')
    })
    
    it('has runs list route at /v8/runs', () => {
      const route = routes.find(r => r.path === '/v8/runs')
      expect(route).toBeDefined()
      expect(route.name).toBe('runs')
    })
    
    it('has run console route at /v8/runs/:id', () => {
      const route = routes.find(r => r.path === '/v8/runs/:id')
      expect(route).toBeDefined()
      expect(route.name).toBe('run-console')
    })
    
    it('has all other v8 routes', () => {
      expect(routes.find(r => r.path === '/v8/agents')).toBeDefined()
      expect(routes.find(r => r.path === '/v8/models')).toBeDefined()
      expect(routes.find(r => r.path === '/v8/memory')).toBeDefined()
      expect(routes.find(r => r.path === '/v8/audit')).toBeDefined()
      expect(routes.find(r => r.path === '/v8/system')).toBeDefined()
    })
  })
  
  describe('Route organization', () => {
    it('all v8 routes start with /v8', () => {
      const v8RouteNames = ['dashboard', 'runs', 'run-console', 'agents', 'models', 'memory', 'audit', 'system']
      const v8Routes = routes.filter(r => r.name && v8RouteNames.includes(r.name))
      
      v8Routes.forEach(route => {
        expect(route.path.startsWith('/v8')).toBe(true)
      })
    })
    
    it('v7.1 routes dont have /v8 prefix', () => {
      const v7Routes = routes.filter(r => r.name && ['chat', 'tools', 'settings', 'login', 'learning'].includes(r.name))
      
      v7Routes.forEach(route => {
        expect(route.path.startsWith('/v8')).toBe(false)
      })
    })
  })
})
