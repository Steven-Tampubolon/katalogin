import * as React from "react"
import { cn } from "@/lib/utils"

export interface SkeletonProps {
  className?: string
  width?: string
  height?: string
}

export const Skeleton = React.forwardRef<HTMLDivElement, SkeletonProps>((props, ref) => {
  return (
    <div
      className={cn(
        "rounded-md h-6 w-full bg-m skewed-overflow",
        props.width && `w-[${props.width}]`,
        props.height && `h-[${props.height}]`,
        props.className,
      )}
      ref={ref}
    />
  )
})

Skeleton.displayName = "Skeleton"