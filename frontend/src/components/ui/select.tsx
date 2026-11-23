import * as React from "react"
import { cn } from "@/lib/utils"

export interface SelectProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string
}

export const Select = React.forwardRef<HTMLDivElement, SelectProps>((props, ref) => {
  return (
    <div
      className={cn(
        "relative",
        props.className,
      )}
      ref={ref}
    />
  )
})

Select.displayName = "Select"