## 2024-05-18 - Replacing Pandas df.apply with Vectorized numpy Operations
**Learning:** Using `df.apply()` row-by-row on a pandas DataFrame is extremely slow because it introduces Python overhead for every single row. Replacing it with vectorized operations (`np.where` or `np.select` over arrays/series) can lead to >10x performance improvements.
**Action:** When creating calculated columns or scores based on multiple conditions across rows, never use `df.apply(axis=1)` if standard vectorized `numpy`/`pandas` methods can achieve the same result. Define conditions as boolean masks and apply values globally.

## 2024-05-22 - Removing redundant pd.to_numeric on np.number dtypes
**Learning:** Selecting columns using `df.select_dtypes(include=[np.number])` guarantees they are already numeric. Applying `pd.to_numeric` on these columns is an expensive, memory-wasting no-op that iterates over the entire DataFrame pointlessly.
**Action:** Remove the redundant `df[numeric_cols].apply(pd.to_numeric, errors='coerce')` step since the data is already numeric, saving unnecessary processing time and memory duplication.

## 2024-05-23 - Vectorizing pandas DataFrame assignments to bypass column alignment
**Learning:** When performing operations on multiple columns (like `grouped[cols].shift(1)` or `grouped[cols].pct_change()`) and assigning the result to a new list of columns with different names (`df[new_cols] = ...`), pandas attempts to align by column names, resulting in a `ValueError` or `NaN`s.
**Action:** Append `.values` to the output of the operation (e.g., `df[new_cols] = grouped[cols].shift(1).values`) to bypass column alignment. This allows replacing multiple slow, individual Series operations with a single, fast DataFrame operation, reducing groupby overhead significantly (~1.4x - 1.8x faster).

## 2024-05-24 - Avoiding groupby agg + merge by using transform
**Learning:** Computing group-level metrics using `df.groupby(...).agg(...)` (e.g. median) and then broadcasting those metrics back to the original DataFrame using `pd.merge()` is slow. It creates intermediate dataframes and requires expensive index alignments. Using `df.groupby(...).transform(...)` is significantly faster because it calculates and broadcasts the metric directly to the original shape in one pass.
**Action:** When you need group-level aggregates aligned to the original rows, replace `groupby` + `merge` patterns with `transform` to save memory and improve performance (~1.5x faster on large datasets).

## 2024-05-30 - Performance Optimization of numpy where string concatenation
**Learning:** In numpy/pandas, doing `np.where(cond, flags + prefix + msg, flags)` where `flags` is an `object` array of strings is surprisingly slow, because it calculates the concatenated strings `flags + prefix + msg` for *all* rows in the array regardless of whether `cond` is true or false. When dealing with string object arrays, this results in significant overhead from unnecessary string allocations and concatenations.
**Action:** Use boolean indexing (`mask = cond; flags[mask] += msg`) to only perform string concatenation on the subset of rows where the condition is actually true. This avoids dense string operations and provides a massive speedup (~3x faster).

## 2024-05-31 - Safe division array operations
**Learning:** Using `np.where(d == 0, 0, n / d)` does not skip calculating `n / d` for zero values. It calculates the entire division array (producing internal warnings and taking extra time), and *then* does the selection. `np.divide(n, d, out=np.zeros_like(n, dtype=float), where=d!=0)` calculates division *only* where the condition holds, bypassing unneeded work and reducing division execution time by >50%.
**Action:** Always use `np.divide` with a `where` clause instead of `np.where` when doing safe division across arrays/series, especially in financial ratio pipelines where division by zero is common.

## 2024-06-03 - Replacing Series Operations with Numpy Arrays for mathematical operations
**Learning:** Performing multiple arithmetic operations on pandas Series variables introduces substantial overhead due to index alignment on every step. For variables drawn from the same DataFrame (which are guaranteed to align), this is entirely unnecessary. Appending `.values` to these Series and working with raw numpy arrays can be ~4x faster.
**Action:** When calculating derived fields using math or building multiple boolean masks from multiple columns of the same DataFrame, append `.values` to bypass pandas overhead.
## 2024-05-28 - Bypassing Pandas Index Alignment Overhead
**Learning:** Pandas incurs significant overhead checking and aligning indices when performing arithmetic operations between two `Series` objects or passing `Series` objects to NumPy functions (like `np.divide`). If the `Series` objects are guaranteed to share the exact same index (e.g. columns from the exact same DataFrame), this check is redundant and very slow.
**Action:** Extract raw NumPy arrays by appending `.values` to Pandas Series before performing vectorized mathematical operations or passing them into numpy functions, especially when dealing with heavy or repeated row-level math in large dataframes.

## 2024-06-05 - Vectorized shifting to bypass Pandas groupby overhead
**Learning:** Even after optimizing `df.groupby(...).shift(1)` to use `.values` (which only skips pandas assignment alignment), the actual `groupby` loop over many groups in Python is inherently slow. If the data is already sorted by group (e.g. `company` and `year`), doing a full-column shift/diff using `numpy` or `pandas` and then masking out the cross-group boundaries using a boolean mask is much faster. Bypassing the groupby logic entirely provides a massive >10x speedup for calculating year-over-year changes or lags.
**Action:** When performing `shift()`, `pct_change()`, or `diff()` on groups inside a sorted dataframe, avoid `groupby(...)` entirely. Instead, calculate a boolean mask that identifies group boundaries (`mask = df['group'].values[1:] != df['group'].values[:-1]`), perform the operation over the entire column using `np.roll` or `.shift().to_numpy()`, and then use the mask to set values that crossed boundaries to `np.nan`.

## 2024-06-07 - Optimizing dataframe missing value replacements with np.nan_to_num
**Learning:** Chaining pandas methods like `df.replace([np.inf, -np.inf], np.nan).fillna(0)` creates multiple intermediate copies of the DataFrame and is slow for large datasets. This is especially true before feeding data into scikit-learn models which typically expect arrays anyway.
**Action:** When you need to replace infs and NaNs with zeros in a dataframe (especially before machine learning), extract the values using `df.to_numpy(copy=True)` and use `np.nan_to_num(arr, copy=False, nan=0.0, posinf=0.0, neginf=0.0)`. This performs all the replacements in a single, fast C-level pass and provides a ~2x performance speedup.
