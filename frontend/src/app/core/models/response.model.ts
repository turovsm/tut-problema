export interface ApiResponseSuccess<T> {
    status: "success" | "error";
    data: T;
    message: string;
}