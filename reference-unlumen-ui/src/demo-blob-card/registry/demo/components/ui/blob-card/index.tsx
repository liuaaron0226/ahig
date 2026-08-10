import {
  BlobCard,
  type BlobCardProps,
} from "@/components/unlumen-ui/blob-card";
import { Button } from "@/components/ui/button";
import Link from "next/link";

import {
  LayoutGridIcon as Blocks,
  CodeSimpleIcon as Code2,
  HeadphonesIcon as Headphones,
  Infinity01Icon as InfinityIcon,
  Refresh03Icon as RefreshCw,
} from "hugeicons-react";

type BlobCardDemoProps = Pick<BlobCardProps, "headerHeight">;

export default function BlobCardDemo({
  headerHeight = 224,
}: BlobCardDemoProps) {
  const PRODUCT_ID =
    process.env.POLAR_PRODUCT_ID ?? "2958d6bb-2b8e-44c3-9404-d42ead77f8fd";

  const FEATURES = [
    { label: "All premium components", icon: Blocks },
    { label: "Future premium releases included", icon: RefreshCw },
    { label: "Full source code and customization", icon: Code2 },
    { label: "Lifetime access. Pay once, own forever.", icon: InfinityIcon },
    { label: "Direct support from the maker", icon: Headphones },
  ];

  return (
    <div className="absolute inset-0 flex w-full items-center justify-center p-8">
      <div className="max-w-sm">
        <BlobCard
          headerHeight={headerHeight}
          header={
            <>
              <span className="text-lg font-serif">
                Pro{" "}
                <span className="text-sm text-foreground/50">
                  {" "}
                  [ Early Supporter Price ]{" "}
                </span>
              </span>
              <div className="mt-2 flex items-baseline gap-3">
                <span className="text-6xl font-medium tracking-tighter">
                  $99
                </span>
                <div className="flex flex-col text-xs leading-snug text-foreground/70">
                  <span className="line-through tracking-wide text-xl">
                    $149
                  </span>
                  <span>One-time payment</span>
                  <span>Lifetime access</span>
                </div>
              </div>
            </>
          }
        >
          <div className="flex w-full items-center justify-center">
            <Button variant="pro" size="lg" className="px-22" asChild>
              <Link href={`/api/checkout?products=${PRODUCT_ID}`}>
                Get Instant Access
              </Link>
            </Button>
          </div>
          <div className="px-8 pt-8 pb-8">
            <ul className="space-y-5">
              {FEATURES.map((f) => (
                <li
                  key={f.label}
                  className="flex items-center gap-4 text-sm text-foreground/80"
                >
                  <f.icon
                    className="size-5 shrink-0 text-foreground/50"
                    strokeWidth={1.5}
                  />
                  {f.label}
                </li>
              ))}
            </ul>
            <p className="mt-8 text-center text-xs text-muted-foreground/80">
              Pay once. Own forever.
            </p>
          </div>
        </BlobCard>
      </div>
    </div>
  );
}
