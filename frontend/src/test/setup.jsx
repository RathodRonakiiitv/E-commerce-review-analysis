import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Global framer-motion mock — returns a proxy that wraps any HTML element
vi.mock('framer-motion', () => {
    const handler = {
        get(_, tag) {
            // Return a component that renders the plain HTML tag
            return ({ children, initial, animate, exit, transition, whileHover, whileTap, whileInView, variants, layout, ...rest }) => {
                // Filter out any remaining framer-motion props
                const cleanProps = {};
                for (const [k, v] of Object.entries(rest)) {
                    if (typeof v !== 'object' || k === 'className' || k === 'style' || k === 'onClick' || k === 'onSubmit' || k === 'onChange' || k === 'onKeyDown' || k === 'onFocus' || k === 'onBlur' || k === 'href' || k === 'to' || k === 'type' || k === 'value' || k === 'placeholder' || k === 'name' || k === 'id' || k === 'disabled' || k === 'title' || k === 'role' || k.startsWith('data-') || k.startsWith('aria-')) {
                        cleanProps[k] = v;
                    } else if (typeof v === 'string' || typeof v === 'number' || typeof v === 'boolean') {
                        cleanProps[k] = v;
                    }
                }
                const Tag = tag;
                return <Tag {...cleanProps}>{children}</Tag>;
            };
        }
    };

    return {
        motion: new Proxy({}, handler),
        AnimatePresence: ({ children }) => <>{children}</>,
        useAnimation: () => ({ start: vi.fn(), set: vi.fn() }),
        useInView: () => true,
    };
});
