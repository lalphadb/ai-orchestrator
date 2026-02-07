import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Toast from '@/components/common/Toast.vue'

describe('Toast Component', () => {
  it('renders when show is true', () => {
    const wrapper = mount(Toast, {
      props: {
        show: true,
        type: 'success',
        message: 'Test message',
      },
    })

    expect(wrapper.find('.fixed').exists()).toBe(true)
    expect(wrapper.text()).toContain('Test message')
  })

  it('does not render when show is false', () => {
    const wrapper = mount(Toast, {
      props: {
        show: false,
        type: 'success',
        message: 'Test message',
      },
    })

    expect(wrapper.find('.fixed').exists()).toBe(false)
  })

  it('applies correct type classes', () => {
    const wrapper = mount(Toast, {
      props: {
        show: true,
        type: 'error',
        message: 'Error occurred',
      },
    })

    expect(wrapper.html()).toContain('bg-red-500/20')
  })

  it('emits close event when close button clicked', async () => {
    const wrapper = mount(Toast, {
      props: {
        show: true,
        type: 'success',
        message: 'Test',
      },
    })

    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('shows description when provided', () => {
    const wrapper = mount(Toast, {
      props: {
        show: true,
        type: 'info',
        message: 'Main message',
        description: 'Additional details',
      },
    })

    expect(wrapper.text()).toContain('Main message')
    expect(wrapper.text()).toContain('Additional details')
  })
})
