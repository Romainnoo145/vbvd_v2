"use client";

import { useState, useEffect } from "react";
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
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TARGET_AUDIENCES } from "@/types/curator";
import { X, Sparkles } from "lucide-react";

const formSchema = z.object({
  theme_title: z.string().min(3, "Title must be at least 3 characters").max(100),
  theme_description: z.string().min(20, "Description must be at least 20 characters").max(1000),
  theme_concepts: z.array(z.string()).min(1, "Add at least one theme concept"),
  reference_artists: z.array(z.string()).min(1, "Add at least one reference artist"),
  target_audience: z.string().min(1, "Please select a target audience"),
  duration_weeks: z.coerce.number().min(1).max(52),
});

type FormValues = z.infer<typeof formSchema>;

export function CuratorForm() {
  const router = useRouter();
  const [conceptInput, setConceptInput] = useState("");
  const [artistInput, setArtistInput] = useState("");
  const [mounted, setMounted] = useState(false);

  // Ensure component only renders on client to avoid hydration mismatch
  useEffect(() => {
    setMounted(true);
  }, []);

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      theme_title: "",
      theme_description: "",
      theme_concepts: [],
      reference_artists: [],
      target_audience: "",
      duration_weeks: 12,
    },
  });

  const addConcept = () => {
    const trimmed = conceptInput.trim();
    if (trimmed && !form.getValues("theme_concepts").includes(trimmed)) {
      form.setValue("theme_concepts", [...form.getValues("theme_concepts"), trimmed]);
      setConceptInput("");
    }
  };

  const removeConcept = (concept: string) => {
    form.setValue(
      "theme_concepts",
      form.getValues("theme_concepts").filter((c) => c !== concept)
    );
  };

  const addArtist = () => {
    const trimmed = artistInput.trim();
    if (trimmed && !form.getValues("reference_artists").includes(trimmed)) {
      form.setValue("reference_artists", [...form.getValues("reference_artists"), trimmed]);
      setArtistInput("");
    }
  };

  const removeArtist = (artist: string) => {
    form.setValue(
      "reference_artists",
      form.getValues("reference_artists").filter((a) => a !== artist)
    );
  };

  const loadDemoData = () => {
    form.setValue("theme_title", "Surrealism and the Unconscious Mind");
    form.setValue("theme_description", "Exploring how surrealist artists used automatism, dream imagery, and psychological symbolism to access the unconscious mind. This exhibition examines the revolutionary artistic movement that emerged in the 1920s, drawing on Freudian psychoanalysis to unlock creative expression beyond rational control.");
    form.setValue("theme_concepts", ["surrealism", "automatism", "dream imagery", "psychoanalysis", "biomorphism", "unconscious mind"]);
    form.setValue("reference_artists", ["Salvador Dalí", "René Magritte", "Max Ernst", "Joan Miró"]);
    form.setValue("target_audience", "general");
    form.setValue("duration_weeks", 12);
  };

  const onSubmit = async (data: FormValues) => {
    // Generate session ID
    const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    // Store curator brief (human-in-the-loop mode always)
    sessionStorage.setItem(`curator_brief_${sessionId}`, JSON.stringify(data));

    // Navigate to generation page
    router.push(`/generate/${sessionId}`);
  };

  if (!mounted) {
    return (
      <Card className="w-full max-w-4xl">
        <CardHeader>
          <CardTitle>Exhibition Curator Brief</CardTitle>
          <CardDescription>
            Describe your exhibition concept and let AI assist in discovering relevant artists and artworks
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4 animate-pulse">
            <div className="h-10 bg-muted rounded" />
            <div className="h-32 bg-muted rounded" />
            <div className="h-10 bg-muted rounded" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-4xl">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle>Exhibition Curator Brief</CardTitle>
            <CardDescription>
              Describe your exhibition concept and let AI assist in discovering relevant artists and artworks
            </CardDescription>
          </div>
          <Button type="button" variant="outline" size="sm" onClick={loadDemoData}>
            <Sparkles className="mr-2 h-4 w-4" />
            Load Demo
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <FormField
              control={form.control}
              name="theme_title"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Exhibition Title</FormLabel>
                  <FormControl>
                    <Input placeholder="e.g., Surrealism in the Digital Age" {...field} />
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
                  <FormLabel>Exhibition Description</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Describe the theme, context, and vision for this exhibition..."
                      className="min-h-[120px]"
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>
                    Provide a detailed description of the exhibition concept
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="theme_concepts"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Theme Concepts</FormLabel>
                  <div className="flex gap-2">
                    <Input
                      placeholder="e.g., dreams, metamorphosis, unconscious"
                      value={conceptInput}
                      onChange={(e) => setConceptInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          e.preventDefault();
                          addConcept();
                        }
                      }}
                    />
                    <Button type="button" onClick={addConcept}>
                      Add
                    </Button>
                  </div>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {field.value.map((concept) => (
                      <Badge key={concept} variant="secondary" className="gap-1">
                        {concept}
                        <X
                          className="h-3 w-3 cursor-pointer"
                          onClick={() => removeConcept(concept)}
                        />
                      </Badge>
                    ))}
                  </div>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="reference_artists"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Reference Artists</FormLabel>
                  <div className="flex gap-2">
                    <Input
                      placeholder="e.g., Salvador Dalí, René Magritte"
                      value={artistInput}
                      onChange={(e) => setArtistInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          e.preventDefault();
                          addArtist();
                        }
                      }}
                    />
                    <Button type="button" onClick={addArtist}>
                      Add
                    </Button>
                  </div>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {field.value.map((artist) => (
                      <Badge key={artist} variant="secondary" className="gap-1">
                        {artist}
                        <X
                          className="h-3 w-3 cursor-pointer"
                          onClick={() => removeArtist(artist)}
                        />
                      </Badge>
                    ))}
                  </div>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="target_audience"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Target Audience</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select audience" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {TARGET_AUDIENCES.map((audience) => (
                          <SelectItem key={audience.value} value={audience.value}>
                            {audience.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="duration_weeks"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Duration (weeks)</FormLabel>
                    <FormControl>
                      <Input type="number" min="1" max="52" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <Button type="submit" className="w-full" size="lg">
              Generate Exhibition Proposal
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
