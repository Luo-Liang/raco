-- for each a, compute max c and the corresponding b (argmax)
select a, b, max(c) from R3 group by a;
