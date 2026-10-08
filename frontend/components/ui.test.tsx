import { render,screen } from "@testing-library/react";
import { describe,expect,it } from "vitest";
import { Pager,Status } from "./ui";
describe("Status",()=>{it("renders pass state",()=>{render(<Status passed/>);expect(screen.getByText("Pass")).toBeInTheDocument()})});
describe("Pager",()=>{it("disables previous on first page",()=>{render(<Pager page={1} total={25} pageSize={20} onChange={()=>{}}/>);expect(screen.getByRole("button",{name:"Previous"})).toBeDisabled();expect(screen.getByText("1 / 2")).toBeInTheDocument()})});
