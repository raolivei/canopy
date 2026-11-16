// Make the jest-dom and jest-axe matcher augmentations visible to `tsc`.
// jest.setup.js imports them at runtime, but as a JavaScript file it does not
// contribute types, so without this file `toBeInTheDocument` and
// `toHaveNoViolations` are unknown to the type checker.
import "@testing-library/jest-dom";
import "jest-axe";
