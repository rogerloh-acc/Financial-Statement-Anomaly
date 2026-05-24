## 2024-05-18 - Replacing Pandas df.apply with Vectorized numpy Operations
**Learning:** Using `df.apply()` row-by-row on a pandas DataFrame is extremely slow because it introduces Python overhead for every single row. Replacing it with vectorized operations (`np.where` or `np.select` over arrays/series) can lead to >10x performance improvements.
**Action:** When creating calculated columns or scores based on multiple conditions across rows, never use `df.apply(axis=1)` if standard vectorized `numpy`/`pandas` methods can achieve the same result. Define conditions as boolean masks and apply values globally.

## 2024-05-22 - Removing redundant pd.to_numeric on np.number dtypes
**Learning:** Selecting columns using `df.select_dtypes(include=[np.number])` guarantees they are already numeric. Applying `pd.to_numeric` on these columns is an expensive, memory-wasting no-op that iterates over the entire DataFrame pointlessly.
**Action:** Remove the redundant `df[numeric_cols].apply(pd.to_numeric, errors='coerce')` step since the data is already numeric, saving unnecessary processing time and memory duplication.

## 2024-05-23 - Vectorizing pandas DataFrame assignments to bypass column alignment
**Learning:** When performing operations on multiple columns (like `grouped[cols].shift(1)` or `grouped[cols].pct_change()`) and assigning the result to a new list of columns with different names (`df[new_cols] = ...`), pandas attempts to align by column names, resulting in a `ValueError` or `NaN`s.
**Action:** Append `.values` to the output of the operation (e.g., `df[new_cols] = grouped[cols].shift(1).values`) to bypass column alignment. This allows replacing multiple slow, individual Series operations with a single, fast DataFrame operation, reducing groupby overhead significantly (~1.4x - 1.8x faster).
