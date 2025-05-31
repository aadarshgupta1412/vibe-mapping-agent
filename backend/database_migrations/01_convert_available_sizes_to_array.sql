-- Migration: Convert available_sizes from text to text array
-- This script converts the comma-separated available_sizes text field to a proper PostgreSQL text array

-- Step 1: Add a new temporary column for the array
ALTER TABLE public.apparels 
ADD COLUMN available_sizes_array text[];

-- Step 2: Update the new column by converting the existing text data
-- This converts "XS,S,M,L,XL" to {"XS","S","M","L","XL"}
UPDATE public.apparels 
SET available_sizes_array = string_to_array(
    REPLACE(REPLACE(available_sizes, ' ', ''), ',', ','), 
    ','
)
WHERE available_sizes IS NOT NULL AND available_sizes != '';

-- Step 3: Handle any null or empty cases
UPDATE public.apparels 
SET available_sizes_array = ARRAY[]::text[]
WHERE available_sizes IS NULL OR available_sizes = '';

-- Step 4: Drop the old column
ALTER TABLE public.apparels 
DROP COLUMN available_sizes;

-- Step 5: Rename the new column to the original name
ALTER TABLE public.apparels 
RENAME COLUMN available_sizes_array TO available_sizes;

-- Step 6: Add a check constraint to ensure valid size values (optional)
ALTER TABLE public.apparels 
ADD CONSTRAINT valid_sizes 
CHECK (
    available_sizes <@ ARRAY['XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL', '2XL', '3XL']::text[]
);

-- Verify the changes
SELECT id, name, available_sizes 
FROM public.apparels 
LIMIT 5; 