# Create New Frontend Component

Create a new React component following project patterns: $ARGUMENTS

## Component Creation Process

1. **Component Analysis**:
   - Analyze component requirements and use cases
   - Determine if it should be in feature-specific or shared location
   - Identify if it should be added to the UI component library
   - Check for existing similar components to avoid duplication

2. **Design System Integration**:
   - Follow existing design patterns in `libs/ui-components`
   - Use Tailwind CSS classes consistently
   - Ensure accessibility compliance (ARIA attributes)
   - Consider responsive design requirements

3. **Component Implementation**:
   - Create component with proper TypeScript types
   - Follow existing naming conventions
   - Include prop validation and default values
   - Add proper error handling and loading states

4. **Storybook Integration**:
   - Create comprehensive Storybook stories
   - Include all component variants and states
   - Add interactive controls for props
   - Document usage examples

5. **Testing**:
   - Write unit tests using React Testing Library
   - Test component behavior and user interactions
   - Include accessibility tests
   - Test error scenarios and edge cases

6. **Documentation**:
   - Add JSDoc comments for all props
   - Include usage examples
   - Document any specific requirements or constraints
   - Update component library documentation if needed

## Component Structure

For feature-specific components:
```
src/features/<feature>/components/
├── ComponentName.tsx
├── ComponentName.test.tsx
├── ComponentName.stories.tsx
└── index.ts
```

For shared components:
```
libs/ui-components/src/lib/component-name/
├── component-name.tsx
├── component-name.test.tsx
├── component-name.stories.tsx
└── index.ts
```

## Quality Checklist

- [ ] Component follows TypeScript best practices
- [ ] All props have explicit types
- [ ] Accessibility requirements met
- [ ] Responsive design implemented
- [ ] Storybook stories created
- [ ] Unit tests written and passing
- [ ] Documentation updated
- [ ] No console errors or warnings