# QA Gate — Runs Before Every Delivery

## Functional Testing
- All features work as described in requirements
- All user interactions work (clicks, forms, navigation, modals)
- All links, buttons, CTAs function correctly
- Form inputs validated with proper error messages
- Edge cases handled: empty states, long text, special characters, missing data

## Responsive Testing
- Mobile (375px), tablet (768px), desktop (1440px+)
- Layouts don't break at in-between breakpoints
- Touch targets minimum 44x44px on mobile

## Performance
- No unnecessary re-renders or redundant API calls
- Images optimized (WebP, lazy loaded)
- No memory leaks or infinite loops
- No render-blocking scripts
- Core Web Vitals: LCP < 2.5s, FID < 100ms, CLS < 0.1

## Code Quality
- No console errors, warnings, or deprecated methods
- Clean, readable, well-commented code
- Proper try/catch error handling
- No hardcoded values that should be env vars
- Semantic HTML throughout

## Accessibility
- ARIA labels on interactive elements
- Alt text on all images
- Keyboard navigation works
- Color contrast meets WCAG AA (4.5:1 minimum)
- Focus indicators visible

## SEO (Websites Only)
- Meta title and description on every page
- Open Graph tags for social sharing
- Structured data / JSON-LD where applicable
- Sitemap.xml generated
- Canonical URLs set
- Heading hierarchy correct (one H1 per page)

## Testing
- Unit tests cover core business logic
- Integration tests verify API endpoints
- Validation tests confirm auth flows and error states
- All tests pass before delivery

## Report Format
```
✅ QA REPORT
Functional:     [PASS/FAIL] — [details]
Responsive:     [PASS/FAIL] — [details]
Performance:    [PASS/FAIL] — [details]
Code Quality:   [PASS/FAIL] — [details]
Accessibility:  [PASS/FAIL] — [details]
SEO:            [PASS/FAIL] — [details]
Tests:          [PASS/FAIL] — [X/Y passing]
Status: [READY TO SHIP / NEEDS FIXES]
```
