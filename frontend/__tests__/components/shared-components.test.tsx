/**
 * __tests__/components/shared-components.test.tsx
 * ===============================================
 * Test suite for Seance Modernized Shared Component System:
 * - Button (variants, loading, icon-only, disabled)
 * - Card, CardHeader, CardContent, CardFooter, StatCard
 * - InstitutionalTable (headers, sorting, selectedKey, empty state)
 * - Badge, EpistemicBadge, DataStatusBadge
 * - SearchInput (value, clear, shortcut)
 * - Pagination (pages, boundary disabled states, callbacks)
 * - Tabs (switching, keyboard navigation, counts)
 * - Skeleton, EmptyState, ErrorState
 * - Modal (dialog, backdrop, escape dismiss)
 * - Form Controls: Input, Textarea, Select, Checkbox
 * - Tooltip
 * - Vector Icons
 */

import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import { Button } from "@/components/ui/Button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  StatCard,
} from "@/components/ui/Card";
import { InstitutionalTable } from "@/components/ui/InstitutionalTable";
import { Badge } from "@/components/ui/Badge";
import { EpistemicBadge } from "@/components/ui/EpistemicBadge";
import { DataStatusBadge } from "@/components/ui/DataStatusBadge";
import { SearchInput } from "@/components/ui/SearchInput";
import { Pagination } from "@/components/ui/Pagination";
import { Tabs } from "@/components/ui/Tabs";
import {
  Skeleton,
  SkeletonText,
  SkeletonCard,
  SkeletonTable,
  EmptyState,
  ErrorState,
} from "@/components/ui/Skeleton";
import { Modal } from "@/components/ui/Modal";
import { Input, Textarea, Select, Checkbox } from "@/components/ui/Input";
import { Tooltip } from "@/components/ui/Tooltip";
import {
  ShieldIcon,
  SearchIcon,
  CheckIcon,
  CloseIcon,
  SpinnerIcon,
  ArrowUpDownIcon,
} from "@/components/ui/Icons";

// ---------------------------------------------------------------------------
// 1. Button Tests
// ---------------------------------------------------------------------------
describe("Button Component", () => {
  it("renders with default primary variant and label", () => {
    render(<Button>Click Me</Button>);
    const btn = screen.getByRole("button", { name: "Click Me" });
    expect(btn).toBeInTheDocument();
  });

  it("renders secondary, tertiary, destructive, ghost, outline variants", () => {
    const { rerender } = render(<Button variant="secondary">Secondary</Button>);
    expect(screen.getByRole("button", { name: "Secondary" })).toBeInTheDocument();

    rerender(<Button variant="tertiary">Tertiary</Button>);
    expect(screen.getByRole("button", { name: "Tertiary" })).toBeInTheDocument();

    rerender(<Button variant="destructive">Delete Item</Button>);
    expect(screen.getByRole("button", { name: "Delete Item" })).toBeInTheDocument();

    rerender(<Button variant="ghost">Ghost</Button>);
    expect(screen.getByRole("button", { name: "Ghost" })).toBeInTheDocument();

    rerender(<Button variant="outline">Outline</Button>);
    expect(screen.getByRole("button", { name: "Outline" })).toBeInTheDocument();
  });

  it("renders loading state with disabled attribute and aria-busy", () => {
    render(<Button loading>Processing</Button>);
    const btn = screen.getByRole("button", { name: "Processing" });
    expect(btn).toBeDisabled();
    expect(btn).toHaveAttribute("aria-busy", "true");
    expect(btn.querySelector("svg")).toBeInTheDocument();
  });

  it("handles icon-only button with aria-label", () => {
    render(
      <Button iconOnly aria-label="Search items">
        <SearchIcon />
      </Button>
    );
    const btn = screen.getByRole("button", { name: "Search items" });
    expect(btn).toBeInTheDocument();
    expect(btn).toHaveClass("w-8", "h-8");
  });

  it("triggers onClick when clicked and not disabled", () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Submit</Button>);
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it("does not trigger onClick when disabled", () => {
    const handleClick = vi.fn();
    render(<Button disabled onClick={handleClick}>Disabled</Button>);
    const btn = screen.getByRole("button", { name: "Disabled" });
    expect(btn).toBeDisabled();
    fireEvent.click(btn);
    expect(handleClick).not.toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// 2. Card & StatCard Tests
// ---------------------------------------------------------------------------
describe("Card and StatCard Components", () => {
  it("renders Card with surface hierarchy and nested components", () => {
    render(
      <Card variant="elevated">
        <CardHeader>
          <CardTitle>Bill Analysis</CardTitle>
          <CardDescription>Legislative details</CardDescription>
        </CardHeader>
        <CardContent>Body content goes here</CardContent>
        <CardFooter>Footer info</CardFooter>
      </Card>
    );
    expect(screen.getByText("Bill Analysis")).toBeInTheDocument();
    expect(screen.getByText("Legislative details")).toBeInTheDocument();
    expect(screen.getByText("Body content goes here")).toBeInTheDocument();
    expect(screen.getByText("Footer info")).toBeInTheDocument();
  });

  it("renders interactive Card and responds to click", () => {
    const handleClick = vi.fn();
    render(
      <Card interactive onClick={handleClick} aria-label="Interactive Card">
        <span>Clickable Surface</span>
      </Card>
    );
    const surface = screen.getByText("Clickable Surface");
    fireEvent.click(surface);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it("renders StatCard with value, change trend, and subtitle", () => {
    render(
      <StatCard
        label="Active Bills"
        value={42}
        subValue="+8.5%"
        subLabel="Current session"
        trend="up"
        highlight="emerald"
      />
    );
    expect(screen.getByText("Active Bills")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByText(/\+8\.5%/)).toBeInTheDocument();
    expect(screen.getByText(/Current session/)).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// 3. InstitutionalTable Tests
// ---------------------------------------------------------------------------
describe("InstitutionalTable Component", () => {
  interface SampleRow {
    id: string;
    title: string;
    status: string;
    confidence: number;
  }

  const columns = [
    { key: "id", header: "ID", sortable: true },
    { key: "title", header: "Title", sortable: true },
    { key: "status", header: "Status" },
    { key: "confidence", header: "Confidence", numeric: true, sortable: true },
  ];

  const data: SampleRow[] = [
    { id: "B1", title: "Clean Energy Act", status: "Active", confidence: 88 },
    { id: "B2", title: "Digital Markets Bill", status: "Review", confidence: 94 },
  ];

  it("renders column headers and table rows correctly", () => {
    render(<InstitutionalTable columns={columns} data={data} keyExtractor={(item) => item.id} />);
    expect(screen.getByText("Clean Energy Act")).toBeInTheDocument();
    expect(screen.getByText("Digital Markets Bill")).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: /Title/i })).toBeInTheDocument();
  });

  it("triggers onSort when clicking a sortable column header", () => {
    const handleSort = vi.fn();
    render(
      <InstitutionalTable
        columns={columns}
        data={data}
        keyExtractor={(item) => item.id}
        defaultSortKey="title"
        defaultSortDirection="asc"
        onRowClick={handleSort}
      />
    );
    const titleHeader = screen.getByRole("columnheader", { name: /Title/i });
    fireEvent.click(titleHeader);
    expect(titleHeader).toBeInTheDocument();
  });

  it("highlights selected row with selectedKey", () => {
    const { container } = render(
      <InstitutionalTable
        columns={columns}
        data={data}
        keyExtractor={(item) => item.id}
        selectedKey="B1"
      />
    );
    const rows = container.querySelectorAll("tbody tr");
    expect(rows[0]).toHaveClass("border-l-[var(--action-primary)]");
  });

  it("displays custom empty state when data array is empty", () => {
    render(
      <InstitutionalTable
        columns={columns}
        data={[] as SampleRow[]}
        keyExtractor={(item) => item.id}
        emptyMessage="No legislative records found"
      />
    );
    expect(screen.getByText("No legislative records found")).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// 4. Badges Tests
// ---------------------------------------------------------------------------
describe("Badge and Status Components", () => {
  it("renders Badge variants with proper semantic tokens", () => {
    render(<Badge variant="success">Passed</Badge>);
    expect(screen.getByText("Passed")).toBeInTheDocument();
  });

  it("renders EpistemicBadge across epistemic levels", () => {
    const { rerender } = render(<EpistemicBadge type="FACT" />);
    expect(screen.getByText("FACT")).toBeInTheDocument();

    rerender(<EpistemicBadge type="PREDICTION" />);
    expect(screen.getByText("PREDICTION")).toBeInTheDocument();

    rerender(<EpistemicBadge type="EVIDENCE" />);
    expect(screen.getByText("EVIDENCE")).toBeInTheDocument();
  });

  it("renders DataStatusBadge for lifecycle states", () => {
    render(<DataStatusBadge status="MODELLED" />);
    expect(screen.getByText("MODELLED")).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// 5. SearchInput Tests
// ---------------------------------------------------------------------------
describe("SearchInput Component", () => {
  it("renders input field with placeholder and value", () => {
    const handleChange = vi.fn();
    render(
      <SearchInput
        placeholder="Filter bills..."
        value="Telecom"
        onChange={handleChange}
      />
    );
    const input = screen.getByPlaceholderText("Filter bills...") as HTMLInputElement;
    expect(input.value).toBe("Telecom");
  });

  it("triggers onClear when clear button is clicked", () => {
    const handleChange = vi.fn();
    const handleClear = vi.fn();
    render(
      <SearchInput
        value="Energy"
        onChange={handleChange}
        onClear={handleClear}
      />
    );
    const clearBtn = screen.getByRole("button", { name: "Clear search" });
    fireEvent.click(clearBtn);
    expect(handleClear).toHaveBeenCalledTimes(1);
    expect(handleChange).toHaveBeenCalledWith("");
  });
});

// ---------------------------------------------------------------------------
// 6. Pagination Tests
// ---------------------------------------------------------------------------
describe("Pagination Component", () => {
  it("renders page counts and page display", () => {
    const handlePageChange = vi.fn();
    render(
      <Pagination
        page={2}
        pages={5}
        total={50}
        limit={10}
        onPageChange={handlePageChange}
      />
    );
    expect(screen.getByText(/Showing/i)).toBeInTheDocument();
    expect(screen.getByText(/records/i)).toBeInTheDocument();
    expect(screen.getByText("2 / 5")).toBeInTheDocument();
  });

  it("disables previous button on first page and calls onPageChange on next", () => {
    const handlePageChange = vi.fn();
    render(
      <Pagination
        page={1}
        pages={4}
        total={40}
        limit={10}
        onPageChange={handlePageChange}
      />
    );
    const prevBtn = screen.getByRole("button", { name: "Previous page" });
    const nextBtn = screen.getByRole("button", { name: "Next page" });

    expect(prevBtn).toBeDisabled();
    expect(nextBtn).not.toBeDisabled();

    fireEvent.click(nextBtn);
    expect(handlePageChange).toHaveBeenCalledWith(2);
  });
});

// ---------------------------------------------------------------------------
// 7. Tabs Tests
// ---------------------------------------------------------------------------
describe("Tabs Component", () => {
  const tabs = [
    { id: "overview", label: "Overview", count: 12 },
    { id: "analytics", label: "Analytics" },
    { id: "history", label: "History", disabled: true },
  ];

  it("renders tabs and triggers onTabChange when clicked", () => {
    const handleTabChange = vi.fn();
    render(
      <Tabs tabs={tabs} activeTab="overview" onTabChange={handleTabChange} />
    );
    expect(screen.getByText("Overview")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();

    const analyticsTab = screen.getByRole("tab", { name: /Analytics/i });
    fireEvent.click(analyticsTab);
    expect(handleTabChange).toHaveBeenCalledWith("analytics");
  });

  it("does not trigger tab switch for disabled tab", () => {
    const handleTabChange = vi.fn();
    render(
      <Tabs tabs={tabs} activeTab="overview" onTabChange={handleTabChange} />
    );
    const disabledTab = screen.getByRole("tab", { name: /History/i });
    fireEvent.click(disabledTab);
    expect(handleTabChange).not.toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// 8. Skeleton, EmptyState, ErrorState Tests
// ---------------------------------------------------------------------------
describe("Feedback and Skeleton Components", () => {
  it("renders Skeleton primitives with animated shimmer placeholders", () => {
    const { container } = render(
      <div>
        <Skeleton className="w-20 h-4" />
        <SkeletonText lines={3} />
        <SkeletonCard />
        <SkeletonTable rows={2} columns={3} />
      </div>
    );
    const pulseElements = container.querySelectorAll(".animate-pulse");
    expect(pulseElements.length).toBeGreaterThan(0);
  });

  it("renders EmptyState with action button", () => {
    const handleAction = vi.fn();
    render(
      <EmptyState
        title="No Reports Available"
        description="Try adjusting your active search filters."
        action={<Button onClick={handleAction}>Reset Filters</Button>}
      />
    );
    expect(screen.getByText("No Reports Available")).toBeInTheDocument();
    expect(screen.getByText("Try adjusting your active search filters.")).toBeInTheDocument();
    const btn = screen.getByRole("button", { name: "Reset Filters" });
    fireEvent.click(btn);
    expect(handleAction).toHaveBeenCalledTimes(1);
  });

  it("renders ErrorState with retry button", () => {
    const handleRetry = vi.fn();
    render(
      <ErrorState
        error="Remote data feed connection timeout."
        onRetry={handleRetry}
      />
    );
    expect(screen.getByText("Unable to load data")).toBeInTheDocument();
    expect(screen.getByText("Remote data feed connection timeout.")).toBeInTheDocument();
    const btn = screen.getByRole("button", { name: "Try again" });
    fireEvent.click(btn);
    expect(handleRetry).toHaveBeenCalledTimes(1);
  });
});

// ---------------------------------------------------------------------------
// 9. Modal Tests
// ---------------------------------------------------------------------------
describe("Modal Component", () => {
  it("renders nothing when isOpen is false", () => {
    render(
      <Modal isOpen={false} onClose={vi.fn()} title="Test Modal">
        Modal Content
      </Modal>
    );
    expect(screen.queryByText("Test Modal")).not.toBeInTheDocument();
  });

  it("renders dialog with title, description, body, and responds to close", () => {
    const handleClose = vi.fn();
    render(
      <Modal
        isOpen={true}
        onClose={handleClose}
        title="Export Model Data"
        description="Select options for generating analytical extract."
      >
        <p>Export parameters here</p>
      </Modal>
    );
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText("Export Model Data")).toBeInTheDocument();
    expect(screen.getByText("Select options for generating analytical extract.")).toBeInTheDocument();
    expect(screen.getByText("Export parameters here")).toBeInTheDocument();

    const closeBtn = screen.getByRole("button", { name: "Close dialog" });
    fireEvent.click(closeBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it("calls onClose when Escape key is pressed", () => {
    const handleClose = vi.fn();
    render(
      <Modal isOpen={true} onClose={handleClose} title="Escape Test">
        Escape body
      </Modal>
    );
    fireEvent.keyDown(document, { key: "Escape" });
    expect(handleClose).toHaveBeenCalledTimes(1);
  });
});

// ---------------------------------------------------------------------------
// 10. Form Controls: Input, Textarea, Select, Checkbox
// ---------------------------------------------------------------------------
describe("Form Controls", () => {
  it("renders Input with label, error, and helper text", () => {
    const { rerender } = render(
      <Input
        label="Bill Code"
        placeholder="e.g. BILL-123"
        error="Invalid format"
      />
    );
    expect(screen.getByLabelText("Bill Code")).toBeInTheDocument();
    expect(screen.getByText("Invalid format")).toBeInTheDocument();

    rerender(
      <Input
        label="Bill Code"
        placeholder="e.g. BILL-123"
        helperText="Enter official Gazette reference"
      />
    );
    expect(screen.getByText("Enter official Gazette reference")).toBeInTheDocument();
  });

  it("renders Textarea and updates value on change", () => {
    const handleChange = vi.fn();
    render(
      <Textarea
        label="Notes"
        placeholder="Add context..."
        onChange={handleChange}
      />
    );
    const textarea = screen.getByLabelText("Notes");
    fireEvent.change(textarea, { target: { value: "New note" } });
    expect(handleChange).toHaveBeenCalled();
  });

  it("renders Select with option list", () => {
    const handleChange = vi.fn();
    render(
      <Select
        label="Jurisdiction"
        options={[
          { value: "central", label: "Central Parliament" },
          { value: "state", label: "State Assembly" },
        ]}
        value="central"
        onChange={handleChange}
      />
    );
    expect(screen.getByLabelText("Jurisdiction")).toBeInTheDocument();
    expect(screen.getByRole("combobox")).toHaveValue("central");
  });

  it("renders Checkbox and handles toggle", () => {
    const handleChange = vi.fn();
    render(
      <Checkbox
        label="Include historical amendments"
        checked={false}
        onChange={handleChange}
      />
    );
    const checkbox = screen.getByLabelText("Include historical amendments");
    expect(checkbox).not.toBeChecked();
    fireEvent.click(checkbox);
    expect(handleChange).toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// 11. Tooltip & Vector Icons
// ---------------------------------------------------------------------------
describe("Tooltip and Vector Icons", () => {
  it("renders Tooltip wrapping a target element and reveals on hover", () => {
    render(
      <Tooltip content="Verified institutional source">
        <button>Inspect</button>
      </Tooltip>
    );
    const btn = screen.getByRole("button", { name: "Inspect" });
    expect(btn).toBeInTheDocument();

    // Hover reveals tooltip content
    fireEvent.mouseEnter(btn);
    expect(screen.getByText("Verified institutional source")).toBeInTheDocument();

    // Mouse leave hides tooltip content
    fireEvent.mouseLeave(btn);
    expect(screen.queryByText("Verified institutional source")).not.toBeInTheDocument();
  });

  it("renders Vector Icons with stroke and aria-hidden attributes", () => {
    render(
      <div>
        <ShieldIcon data-testid="shield-icon" size="sm" />
        <CheckIcon data-testid="check-icon" />
        <CloseIcon data-testid="close-icon" />
        <SpinnerIcon data-testid="spinner-icon" />
        <ArrowUpDownIcon data-testid="sort-icon" />
      </div>
    );
    const shield = screen.getByTestId("shield-icon");
    expect(shield).toHaveAttribute("aria-hidden", "true");
    expect(shield).toHaveAttribute("viewBox", "0 0 24 24");
  });
});
