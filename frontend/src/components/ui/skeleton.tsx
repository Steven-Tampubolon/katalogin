import * as React from "react"

export const Skeleton = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>((props, ref) => {
  return (
    <div
      className={cn(
        "rounded-md h-6 w-full bg-base-200/60 animate-pulse",
        props.className,
      )}
      ref={ref}
    )
  )
})

Skeleton.displayName = "Skeleton"