"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Loader2, X, Check, ChevronsUpDown, ArrowLeft, Sparkles, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

// Form Schema
const formSchema = z.object({
  theme_title: z.string().min(1, "Titel is verplicht"),
  theme_description: z.string().optional(),
  art_movements: z.array(z.string()).max(5, "Maximum 5 stromingen"),
  media_types: z.array(z.string()).max(5, "Maximum 5 media"),
  time_period: z.string(),
  geographic_focus: z.array(z.string()).min(1, "Selecteer minimaal 1 land"),
  extra_countries: z.string().optional(),
  target_audience: z.string(),
  duration_weeks: z.coerce.number().min(2).max(52),
});

type FormValues = z.infer<typeof formSchema>;

const LOCALE_STORAGE_KEY = "curator_form_state";

const EU_COUNTRIES = [
  { value: "Netherlands", label: "🇳🇱 Nederland", default: true },
  { value: "Belgium", label: "🇧🇪 België", default: true },
  { value: "Germany", label: "🇩🇪 Duitsland", default: true },
  { value: "France", label: "🇫🇷 Frankrijk", default: false },
  { value: "Spain", label: "🇪🇸 Spanje", default: false },
  { value: "Italy", label: "🇮🇹 Italië", default: false },
  { value: "Poland", label: "🇵🇱 Polen", default: false },
  { value: "Sweden", label: "🇸🇪 Zweden", default: false },
];

// Demo data for quick testing
const DEMO_DATA: FormValues = {
  theme_title: "Surrealisme in het Digitale Tijdperk",
  theme_description: "Een tentoonstelling die de invloed van surrealistische principes op hedendaagse digitale kunst onderzoekt.",
  art_movements: ["surrealism", "contemporary"],
  media_types: ["photography", "video_art", "installation"],
  time_period: "contemporary",
  geographic_focus: ["Netherlands", "Belgium", "Germany", "France"],
  extra_countries: "",
  target_audience: "general",
  duration_weeks: 16,
};

export function CuratorForm() {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);

  const wsRef = useRef<WebSocket | null>(null);
  const sessionIdRef = useRef<string | null>(null);

  // Combobox states
  const [openMovements, setOpenMovements] = useState(false);
  const [openMedia, setOpenMedia] = useState(false);

  // Categories from API
  const [categories, setCategories] = useState<{
    time_periods: Array<{ value: string; label: string }>;
    art_movements: Array<{ value: string; label: string }>;
    media_types: Array<{ value: string; label: string; priority: boolean }>;
  }>({
    time_periods: [],
    art_movements: [],
    media_types: [],
  });

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      theme_title: "",
      theme_description: "",
      art_movements: [],
      media_types: [],
      time_period: "contemporary",
      geographic_focus: ["Netherlands", "Belgium", "Germany"],
      extra_countries: "",
      target_audience: "general",
      duration_weeks: 12,
    },
  });

  // Fetch categories
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
        const response = await fetch(`${API_BASE}/api/categories`);
        if (response.ok) {
          const data = await response.json();
          setCategories(data);
        }
      } catch (error) {
        console.error("Failed to fetch categories:", error);
      }
    };
    fetchCategories();
  }, []);

  // Load from localStorage
  useEffect(() => {
    setMounted(true);
    const saved = localStorage.getItem(LOCALE_STORAGE_KEY);
    if (saved) {
      try {
        const data = JSON.parse(saved);
        form.reset(data);
      } catch (error) {
        console.error("Failed to load saved state:", error);
      }
    }
  }, [form]);

  // Save to localStorage
  useEffect(() => {
    if (!mounted) return;
    const subscription = form.watch((values) => {
      localStorage.setItem(LOCALE_STORAGE_KEY, JSON.stringify(values));
    });
    return () => subscription.unsubscribe();
  }, [form, mounted]);

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const loadDemo = () => {
    form.reset(DEMO_DATA);
    setCurrentStep(1);
  };


  const onSubmit = async (data: FormValues) => {
    setIsSubmitting(true);

    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
      const response = await fetch(`${API_BASE}/api/curator/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          curator_brief: data,
          config: { phase: "theme_only" },
        }),
      });

      if (!response.ok) throw new Error(`Failed to submit: ${response.statusText}`);

      const result = await response.json();

      // Navigate to refine-theme page with session_id
      if (result.session_id) {
        sessionIdRef.current = result.session_id;
        router.push(`/refine-theme/${result.session_id}`);
      } else {
        throw new Error("No session_id received from server");
      }
    } catch (error) {
      console.error("Failed to submit:", error);
      alert("Kon voorstel niet genereren. Controleer je verbinding of probeer later opnieuw.");
      setIsSubmitting(false);
    }
    // Note: Don't set isSubmitting(false) on success - let navigation happen
  };

  const nextStep = async () => {
    const fields = currentStep === 1
      ? ["theme_title", "art_movements", "media_types", "time_period"]
      : [];

    const isValid = await form.trigger(fields as any);
    if (isValid) setCurrentStep(2);
  };

  const prevStep = () => setCurrentStep(1);

  if (!mounted) {
    return (
      <Card className="w-full max-w-2xl mx-auto">
        <CardContent className="pt-6">
          <div className="space-y-4 animate-pulse">
            <div className="h-10 bg-neutral-100 rounded" />
            <div className="h-32 bg-neutral-100 rounded" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="w-full max-w-2xl mx-auto space-y-6">
      <Card className="relative border-neutral-200 bg-white shadow-lg">
        {/* Progress Bar */}
        <div className="absolute inset-x-0 top-0 h-1 bg-neutral-100">
          <div
            className="h-full bg-[var(--brand-primary)] transition-all duration-300"
            style={{ width: `${(currentStep / 2) * 100}%` }}
          />
        </div>

        <CardHeader className="pt-8">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-2xl text-[var(--brand-ink)]">
                Tentoonstellingsbrief
              </CardTitle>
              <CardDescription className="text-[var(--brand-muted)] mt-2">
                Stap {currentStep} van 2
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              {currentStep === 1 && (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={loadDemo}
                  className="text-[var(--brand-primary)] border-[var(--brand-primary)]"
                >
                  <Zap className="mr-2 h-4 w-4" />
                  Demo laden
                </Button>
              )}
              {currentStep === 2 && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={prevStep}
                  className="text-[var(--brand-muted)]"
                >
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  Vorige
                </Button>
              )}
            </div>
          </div>
        </CardHeader>

        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              {/* Step 1: Tentoonstelling */}
              {currentStep === 1 && (
                <div className="space-y-6 animate-in fade-in duration-300">
                  <FormField
                    control={form.control}
                    name="theme_title"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="text-base">Titel van de tentoonstelling *</FormLabel>
                        <FormControl>
                          <Input
                            placeholder="Bijv. Surrealisme in het Digitale Tijdperk"
                            className="text-lg h-12"
                            {...field}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="theme_description"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Beschrijving (optioneel)</FormLabel>
                        <FormControl>
                          <Textarea
                            placeholder="Korte context over het thema..."
                            className="min-h-[80px] resize-none"
                            {...field}
                          />
                        </FormControl>
                        <FormDescription className="text-xs">
                          Beschrijf kort het thema en de aanleiding
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  {/* Combined Movements & Media Combobox */}
                  <div className="space-y-4">
                    <FormField
                      control={form.control}
                      name="art_movements"
                      render={({ field }) => (
                        <FormItem className="flex flex-col">
                          <FormLabel>Kunststromingen</FormLabel>
                          <Popover open={openMovements} onOpenChange={setOpenMovements}>
                            <PopoverTrigger asChild>
                              <FormControl>
                                <Button
                                  variant="outline"
                                  role="combobox"
                                  className={cn(
                                    "justify-between h-auto min-h-[40px] py-2",
                                    !field.value?.length && "text-muted-foreground"
                                  )}
                                >
                                  {field.value?.length ? (
                                    <div className="flex flex-wrap gap-1">
                                      {field.value.map((val) => {
                                        const movement = categories.art_movements.find(m => m.value === val);
                                        return (
                                          <Badge key={val} variant="secondary" className="mr-1">
                                            {movement?.label}
                                            <button
                                              type="button"
                                              className="ml-1 hover:text-destructive"
                                              onClick={(e) => {
                                                e.stopPropagation();
                                                field.onChange(field.value?.filter(v => v !== val));
                                              }}
                                            >
                                              <X className="h-3 w-3" />
                                            </button>
                                          </Badge>
                                        );
                                      })}
                                    </div>
                                  ) : (
                                    "Zoek en selecteer stromingen..."
                                  )}
                                  <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                                </Button>
                              </FormControl>
                            </PopoverTrigger>
                            <PopoverContent className="w-[400px] p-0" align="start">
                              <Command>
                                <CommandInput placeholder="Zoek stroming..." />
                                <CommandList>
                                  <CommandEmpty>Geen stroming gevonden.</CommandEmpty>
                                  <CommandGroup>
                                    {categories.art_movements.map((movement) => {
                                      const isSelected = field.value?.includes(movement.value);
                                      const isDisabled = !isSelected && (field.value?.length || 0) >= 5;

                                      return (
                                        <CommandItem
                                          key={movement.value}
                                          value={movement.value}
                                          disabled={isDisabled}
                                          onSelect={() => {
                                            if (isSelected) {
                                              field.onChange(field.value?.filter(v => v !== movement.value));
                                            } else if (!isDisabled) {
                                              field.onChange([...(field.value || []), movement.value]);
                                            }
                                          }}
                                        >
                                          <Check
                                            className={cn(
                                              "mr-2 h-4 w-4",
                                              isSelected ? "opacity-100" : "opacity-0"
                                            )}
                                          />
                                          {movement.label}
                                        </CommandItem>
                                      );
                                    })}
                                  </CommandGroup>
                                </CommandList>
                              </Command>
                            </PopoverContent>
                          </Popover>
                          <FormDescription className="text-xs">
                            {field.value?.length || 0}/5 stromingen geselecteerd
                          </FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="media_types"
                      render={({ field }) => (
                        <FormItem className="flex flex-col">
                          <FormLabel>Media types</FormLabel>
                          <Popover open={openMedia} onOpenChange={setOpenMedia}>
                            <PopoverTrigger asChild>
                              <FormControl>
                                <Button
                                  variant="outline"
                                  role="combobox"
                                  className={cn(
                                    "justify-between h-auto min-h-[40px] py-2",
                                    !field.value?.length && "text-muted-foreground"
                                  )}
                                >
                                  {field.value?.length ? (
                                    <div className="flex flex-wrap gap-1">
                                      {field.value.map((val) => {
                                        const media = categories.media_types.find(m => m.value === val);
                                        return (
                                          <Badge
                                            key={val}
                                            variant="secondary"
                                            className={cn(
                                              "mr-1",
                                              media?.priority && "border-[var(--brand-primary)]"
                                            )}
                                          >
                                            {media?.label}
                                            {media?.priority && <span className="ml-1">★</span>}
                                            <button
                                              type="button"
                                              className="ml-1 hover:text-destructive"
                                              onClick={(e) => {
                                                e.stopPropagation();
                                                field.onChange(field.value?.filter(v => v !== val));
                                              }}
                                            >
                                              <X className="h-3 w-3" />
                                            </button>
                                          </Badge>
                                        );
                                      })}
                                    </div>
                                  ) : (
                                    "Zoek en selecteer media..."
                                  )}
                                  <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                                </Button>
                              </FormControl>
                            </PopoverTrigger>
                            <PopoverContent className="w-[400px] p-0" align="start">
                              <Command>
                                <CommandInput placeholder="Zoek media type..." />
                                <CommandList>
                                  <CommandEmpty>Geen media type gevonden.</CommandEmpty>
                                  <CommandGroup>
                                    {categories.media_types.map((media) => {
                                      const isSelected = field.value?.includes(media.value);
                                      const isDisabled = !isSelected && (field.value?.length || 0) >= 5;

                                      return (
                                        <CommandItem
                                          key={media.value}
                                          value={media.value}
                                          disabled={isDisabled}
                                          onSelect={() => {
                                            if (isSelected) {
                                              field.onChange(field.value?.filter(v => v !== media.value));
                                            } else if (!isDisabled) {
                                              field.onChange([...(field.value || []), media.value]);
                                            }
                                          }}
                                        >
                                          <Check
                                            className={cn(
                                              "mr-2 h-4 w-4",
                                              isSelected ? "opacity-100" : "opacity-0"
                                            )}
                                          />
                                          {media.label}
                                          {media.priority && <span className="ml-1 text-xs">★</span>}
                                        </CommandItem>
                                      );
                                    })}
                                  </CommandGroup>
                                </CommandList>
                              </Command>
                            </PopoverContent>
                          </Popover>
                          <FormDescription className="text-xs">
                            {field.value?.length || 0}/5 media types geselecteerd (★ = Van Bommel focus)
                          </FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  <FormField
                    control={form.control}
                    name="time_period"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Tijdsperiode</FormLabel>
                        <FormControl>
                          <div className="grid grid-cols-2 gap-3 pt-2">
                            {categories.time_periods.map((period) => {
                              const isSelected = field.value === period.value;
                              return (
                                <div
                                  key={period.value}
                                  onClick={() => field.onChange(period.value)}
                                  className={cn(
                                    "relative cursor-pointer rounded-lg border-2 p-4 hover:bg-neutral-50 transition-all",
                                    isSelected
                                      ? "border-[var(--brand-primary)] bg-[var(--brand-primary)]/5"
                                      : "border-neutral-200"
                                  )}
                                >
                                  <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                      <div className="font-medium text-sm text-[var(--brand-ink)]">
                                        {period.label}
                                      </div>
                                      <div className="text-xs text-[var(--brand-muted)] mt-1">
                                        {period.years.start}–{period.years.end}
                                      </div>
                                    </div>
                                    <div
                                      className={cn(
                                        "h-4 w-4 rounded-full border-2 flex items-center justify-center",
                                        isSelected
                                          ? "border-[var(--brand-primary)]"
                                          : "border-neutral-300"
                                      )}
                                    >
                                      {isSelected && (
                                        <div className="h-2 w-2 rounded-full bg-[var(--brand-primary)]" />
                                      )}
                                    </div>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <Button
                    type="button"
                    onClick={nextStep}
                    className="w-full bg-[var(--brand-primary)] hover:bg-[var(--brand-primary)]/90"
                    size="lg"
                  >
                    Volgende: Details
                  </Button>
                </div>
              )}

              {/* Step 2: Details */}
              {currentStep === 2 && (
                <div className="space-y-6 animate-in fade-in duration-300">
                  <FormField
                    control={form.control}
                    name="geographic_focus"
                    render={() => (
                      <FormItem>
                        <FormLabel>Collectiebronnen (landen)</FormLabel>
                        <FormDescription className="text-xs mb-3">
                          Uit welke landen wil je kunstwerken & kunstenaars ontdekken?
                        </FormDescription>
                        <div className="grid grid-cols-3 gap-3 pt-2">
                          {EU_COUNTRIES.map((country) => (
                            <FormField
                              key={country.value}
                              control={form.control}
                              name="geographic_focus"
                              render={({ field }) => (
                                <FormItem
                                  key={country.value}
                                  className="flex flex-row items-center space-x-2 space-y-0"
                                >
                                  <FormControl>
                                    <Checkbox
                                      checked={field.value?.includes(country.value)}
                                      onCheckedChange={(checked) => {
                                        const current = field.value || [];
                                        field.onChange(
                                          checked
                                            ? [...current, country.value]
                                            : current.filter((v) => v !== country.value)
                                        );
                                      }}
                                    />
                                  </FormControl>
                                  <FormLabel className="font-normal cursor-pointer">
                                    {country.label}
                                  </FormLabel>
                                </FormItem>
                              )}
                            />
                          ))}
                        </div>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="extra_countries"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Aanvullende landen (optioneel)</FormLabel>
                        <FormControl>
                          <Input
                            placeholder="bijv. Verenigd Koninkrijk, Zwitserland, Verenigde Staten"
                            {...field}
                          />
                        </FormControl>
                        <FormDescription className="text-xs">
                          Kommagescheiden landen buiten bovenstaande selectie
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="target_audience"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Doelgroep</FormLabel>
                        <FormControl>
                          <div className="grid grid-cols-2 gap-3 pt-2">
                            {[
                              { value: "general", label: "Kunstliefhebbers", description: "Breed publiek" },
                              { value: "academic", label: "Professionals", description: "Curators & experts" },
                              { value: "youth", label: "Studenten", description: "Onderwijs & academisch" },
                              { value: "family", label: "Families", description: "Toegankelijk voor iedereen" },
                            ].map((audience) => {
                              const isSelected = field.value === audience.value;
                              return (
                                <div
                                  key={audience.value}
                                  onClick={() => field.onChange(audience.value)}
                                  className={cn(
                                    "relative cursor-pointer rounded-lg border-2 p-3 hover:bg-neutral-50 transition-all",
                                    isSelected
                                      ? "border-[var(--brand-primary)] bg-[var(--brand-primary)]/5"
                                      : "border-neutral-200"
                                  )}
                                >
                                  <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                      <div className="font-medium text-sm text-[var(--brand-ink)]">
                                        {audience.label}
                                      </div>
                                      <div className="text-xs text-[var(--brand-muted)] mt-0.5">
                                        {audience.description}
                                      </div>
                                    </div>
                                    <div
                                      className={cn(
                                        "h-4 w-4 rounded-full border-2 flex items-center justify-center shrink-0 ml-2",
                                        isSelected
                                          ? "border-[var(--brand-primary)]"
                                          : "border-neutral-300"
                                      )}
                                    >
                                      {isSelected && (
                                        <div className="h-2 w-2 rounded-full bg-[var(--brand-primary)]" />
                                      )}
                                    </div>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="duration_weeks"
                    render={({ field }) => (
                      <FormItem>
                        <div className="flex items-center gap-4">
                          <FormLabel className="whitespace-nowrap">Duur (weken)</FormLabel>
                          <FormControl>
                            <Input
                              type="number"
                              min="2"
                              max="52"
                              className="w-20"
                              {...field}
                              onChange={(e) => field.onChange(parseInt(e.target.value))}
                            />
                          </FormControl>
                        </div>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <Button
                    type="submit"
                    disabled={isSubmitting}
                    className="w-full bg-[var(--brand-primary)] hover:bg-[var(--brand-primary)]/90"
                    size="lg"
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Voorstel genereren...
                      </>
                    ) : (
                      <>
                        <Sparkles className="mr-2 h-4 w-4" />
                        Genereer voorstel
                      </>
                    )}
                  </Button>
                  <p className="text-xs text-center text-[var(--brand-muted)]">
                    Je kunt direct bekijken en bijstellen — niets wordt definitief opgeslagen.
                  </p>
                </div>
              )}
            </form>
          </Form>
        </CardContent>
      </Card>

    </div>
  );
}
